import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from categories.models import Category
from inventory.models import Inventory
from products.models import Product, ProductItem
from users.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_user():
    return User.objects.create_user(email="customer@test.com", password="12345678")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@test.com",
        password="12345678",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def product_item():
    category = Category.objects.create(name="Accessories", slug="accessories")
    product = Product.objects.create(category=category, name="Bag")
    return ProductItem.objects.create(
        product=product,
        sku="BAG-001",
        name="Blue bag",
        price=Decimal("25.00"),
    )


@pytest.fixture
def inventory(product_item):
    return Inventory.objects.create(product_item=product_item, quantity=4)


def authenticate(api_client, user):
    api_client.force_authenticate(user=user)


@pytest.mark.django_db
def test_public_inventory_read_exposes_availability_but_not_quantity(
    api_client, inventory
):
    response = api_client.get(f"/api/v1/inventory/{inventory.pk}/")

    assert response.status_code == 200
    assert response.data["id"] == str(inventory.pk)
    assert response.data["product_item"] == inventory.product_item_id
    assert response.data["in_stock"] is True
    assert "quantity" not in response.data


@pytest.mark.django_db
def test_public_inventory_read_marks_zero_quantity_unavailable(
    api_client, product_item
):
    inventory = Inventory.objects.create(product_item=product_item, quantity=0)

    response = api_client.get(f"/api/v1/inventory/{inventory.pk}/")

    assert response.status_code == 200
    assert response.data["in_stock"] is False
    assert "quantity" not in response.data


@pytest.mark.django_db
def test_public_inventory_list_hides_inactive_product_items_and_parents(
    api_client, inventory
):
    inactive_item = ProductItem.objects.create(
        product=inventory.product_item.product,
        sku="BAG-INACTIVE",
        name="Inactive bag",
        price=Decimal("26.00"),
        is_active=False,
    )
    inactive_item_inventory = Inventory.objects.create(
        product_item=inactive_item,
        quantity=7,
    )
    inactive_product = Product.objects.create(
        category=inventory.product_item.product.category,
        name="Inactive product",
        is_active=False,
    )
    inactive_product_item = ProductItem.objects.create(
        product=inactive_product,
        sku="INACTIVE-PRODUCT-ITEM",
        name="Item from inactive product",
        price=Decimal("28.00"),
    )
    inactive_product_inventory = Inventory.objects.create(
        product_item=inactive_product_item,
        quantity=2,
    )

    response = api_client.get("/api/v1/inventory/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(inventory.pk)
    assert "quantity" not in response.data["results"][0]
    assert (
        api_client.get(f"/api/v1/inventory/{inactive_item_inventory.pk}/").status_code
        == 404
    )
    assert (
        api_client.get(
            f"/api/v1/inventory/{inactive_product_inventory.pk}/"
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_admin_inventory_read_includes_exact_quantity(
    api_client, admin_user, inventory
):
    authenticate(api_client, admin_user)

    response = api_client.get(f"/api/v1/inventory/{inventory.pk}/")
    list_response = api_client.get("/api/v1/inventory/")

    assert response.status_code == 200
    assert response.data["quantity"] == 4
    assert response.data["in_stock"] is True
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["quantity"] == 4


@pytest.mark.django_db
def test_admin_creates_and_adjusts_inventory_quantity(
    api_client, admin_user, product_item
):
    authenticate(api_client, admin_user)

    create_response = api_client.post(
        "/api/v1/inventory/",
        {"product_item": str(product_item.pk), "quantity": 5},
        format="json",
    )
    update_response = api_client.patch(
        f"/api/v1/inventory/{create_response.data['id']}/",
        {"quantity": 0},
        format="json",
    )

    assert create_response.status_code == 201
    assert uuid.UUID(create_response.data["id"])
    assert create_response.data["quantity"] == 5
    assert update_response.status_code == 200
    assert update_response.data["quantity"] == 0
    assert update_response.data["in_stock"] is False


@pytest.mark.django_db
def test_inventory_update_cannot_reassign_product_item(
    api_client, admin_user, inventory
):
    another_product_item = ProductItem.objects.create(
        product=inventory.product_item.product,
        sku="BAG-002",
        name="Red bag",
        price=Decimal("27.00"),
    )
    authenticate(api_client, admin_user)

    response = api_client.patch(
        f"/api/v1/inventory/{inventory.pk}/",
        {"product_item": str(another_product_item.pk)},
        format="json",
    )

    assert response.status_code == 400
    assert "product_item" in response.data
    inventory.refresh_from_db()
    assert inventory.product_item_id != another_product_item.pk


@pytest.mark.django_db
def test_non_admin_cannot_write_inventory(api_client, customer_user, product_item):
    payload = {"product_item": str(product_item.pk), "quantity": 3}
    anonymous_response = api_client.post(
        "/api/v1/inventory/",
        payload,
        format="json",
    )
    authenticate(api_client, customer_user)
    customer_response = api_client.post(
        "/api/v1/inventory/",
        payload,
        format="json",
    )

    assert anonymous_response.status_code == 401
    assert customer_response.status_code == 403


@pytest.mark.django_db
def test_inventory_rejects_negative_quantity_duplicate_item_and_unknown_item(
    api_client, admin_user, inventory
):
    authenticate(api_client, admin_user)
    duplicate_item_response = api_client.post(
        "/api/v1/inventory/",
        {"product_item": str(inventory.product_item_id), "quantity": 8},
        format="json",
    )
    negative_quantity_response = api_client.post(
        "/api/v1/inventory/",
        {"product_item": str(uuid.uuid4()), "quantity": -1},
        format="json",
    )
    unknown_item_response = api_client.post(
        "/api/v1/inventory/",
        {"product_item": str(uuid.uuid4()), "quantity": 2},
        format="json",
    )

    assert duplicate_item_response.status_code == 400
    assert "product_item" in duplicate_item_response.data
    assert negative_quantity_response.status_code == 400
    assert "quantity" in negative_quantity_response.data
    assert unknown_item_response.status_code == 400
    assert "product_item" in unknown_item_response.data


@pytest.mark.django_db
def test_inventory_delete_and_full_update_are_not_exposed(
    api_client, admin_user, inventory
):
    authenticate(api_client, admin_user)

    delete_response = api_client.delete(f"/api/v1/inventory/{inventory.pk}/")
    put_response = api_client.put(
        f"/api/v1/inventory/{inventory.pk}/",
        {"quantity": 2},
        format="json",
    )

    assert delete_response.status_code == 405
    assert put_response.status_code == 405


@pytest.mark.django_db
def test_inventory_database_constraint_rejects_negative_quantity(product_item):
    with transaction.atomic(), pytest.raises(IntegrityError):
        Inventory.objects.create(product_item=product_item, quantity=-1)

    Inventory.objects.create(product_item=product_item, quantity=0)
    with transaction.atomic(), pytest.raises(IntegrityError):
        Inventory.objects.create(product_item=product_item, quantity=3)
