import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from rest_framework.test import APIClient

from categories.models import Category
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
def category():
    return Category.objects.create(name="Accessories", slug="accessories")


@pytest.fixture
def product(category):
    return Product.objects.create(category=category, name="Bag")


def authenticate(api_client, user):
    api_client.force_authenticate(user=user)


@pytest.mark.django_db
def test_public_product_list_shows_active_products_with_pagination(
    api_client, category
):
    active_product = Product.objects.create(category=category, name="Active bag")
    Product.objects.create(category=category, name="Inactive bag", is_active=False)

    response = api_client.get("/api/v1/products/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(active_product.pk)
    assert response.data["results"][0]["category"] == category.pk


@pytest.mark.django_db
def test_public_product_item_list_requires_active_item_and_product(
    api_client, category
):
    active_product = Product.objects.create(category=category, name="Active bag")
    inactive_product = Product.objects.create(
        category=category,
        name="Inactive bag",
        is_active=False,
    )
    active_item = ProductItem.objects.create(
        product=active_product,
        sku="BAG-ACTIVE",
        name="Active bag SKU",
        price=Decimal("25.00"),
    )
    ProductItem.objects.create(
        product=active_product,
        sku="BAG-INACTIVE",
        name="Inactive bag SKU",
        price=Decimal("26.00"),
        is_active=False,
    )
    ProductItem.objects.create(
        product=inactive_product,
        sku="BAG-OLD-PRODUCT",
        name="Item from inactive product",
        price=Decimal("27.00"),
    )

    response = api_client.get("/api/v1/product-items/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(active_item.pk)


@pytest.mark.django_db
def test_api_admin_can_read_inactive_products_and_items(
    api_client, admin_user, category
):
    product = Product.objects.create(
        category=category,
        name="Inactive bag",
        is_active=False,
    )
    item = ProductItem.objects.create(
        product=product,
        sku="BAG-ADMIN",
        name="Inactive bag SKU",
        price=Decimal("25.00"),
        is_active=False,
    )
    authenticate(api_client, admin_user)

    products_response = api_client.get("/api/v1/products/")
    items_response = api_client.get("/api/v1/product-items/")

    assert products_response.data["count"] == 1
    assert products_response.data["results"][0]["id"] == str(product.pk)
    assert items_response.data["count"] == 1
    assert items_response.data["results"][0]["id"] == str(item.pk)


@pytest.mark.django_db
def test_customer_cannot_create_or_update_catalog_resources(
    api_client, customer_user, product
):
    item = ProductItem.objects.create(
        product=product,
        sku="CUSTOMER-FORBIDDEN",
        name="Customer item",
        price=Decimal("10.00"),
    )
    authenticate(api_client, customer_user)

    create_response = api_client.post(
        "/api/v1/products/",
        {"category": str(product.category_id), "name": "Another bag"},
        format="json",
    )
    update_response = api_client.patch(
        f"/api/v1/products/{product.pk}/",
        {"name": "Changed bag"},
        format="json",
    )
    item_update_response = api_client.patch(
        f"/api/v1/product-items/{item.pk}/",
        {"name": "Changed item"},
        format="json",
    )

    assert create_response.status_code == 403
    assert update_response.status_code == 403
    assert item_update_response.status_code == 403


@pytest.mark.django_db
def test_admin_creates_product_and_product_item_with_uuid_relations(
    api_client, admin_user, category
):
    authenticate(api_client, admin_user)

    product_response = api_client.post(
        "/api/v1/products/",
        {
            "category": str(category.pk),
            "name": "Travel bag",
            "description": "Lightweight bag",
        },
        format="json",
    )
    item_response = api_client.post(
        "/api/v1/product-items/",
        {
            "product": product_response.data["id"],
            "sku": "TRAVEL-BAG-001",
            "name": "Blue travel bag",
            "price": "49.90",
        },
        format="json",
    )

    assert product_response.status_code == 201
    assert uuid.UUID(product_response.data["id"])
    assert product_response.data["category"] == category.pk
    assert item_response.status_code == 201
    assert uuid.UUID(item_response.data["id"])
    assert item_response.data["product"] == uuid.UUID(product_response.data["id"])
    assert item_response.data["price"] == "49.90"
    assert ProductItem.objects.get(sku="TRAVEL-BAG-001").price == Decimal("49.90")


@pytest.mark.django_db
def test_product_item_rejects_negative_price_duplicate_sku_and_unknown_product(
    api_client, admin_user, product
):
    ProductItem.objects.create(
        product=product,
        sku="EXISTING-SKU",
        name="Existing item",
        price=Decimal("10.00"),
    )
    authenticate(api_client, admin_user)
    base_payload = {
        "product": str(product.pk),
        "name": "New item",
        "price": "12.00",
    }

    negative_price_response = api_client.post(
        "/api/v1/product-items/",
        {**base_payload, "sku": "NEGATIVE-SKU", "price": "-1.00"},
        format="json",
    )
    duplicate_sku_response = api_client.post(
        "/api/v1/product-items/",
        {**base_payload, "sku": "EXISTING-SKU"},
        format="json",
    )
    unknown_product_response = api_client.post(
        "/api/v1/product-items/",
        {**base_payload, "sku": "UNKNOWN-PRODUCT", "product": str(uuid.uuid4())},
        format="json",
    )

    assert negative_price_response.status_code == 400
    assert "price" in negative_price_response.data
    assert duplicate_sku_response.status_code == 400
    assert "sku" in duplicate_sku_response.data
    assert unknown_product_response.status_code == 400
    assert "product" in unknown_product_response.data


@pytest.mark.django_db
def test_product_and_item_updates_are_partial_and_delete_is_not_exposed(
    api_client, admin_user, product
):
    item = ProductItem.objects.create(
        product=product,
        sku="PATCHABLE-SKU",
        name="Patchable item",
        price=Decimal("10.00"),
    )
    authenticate(api_client, admin_user)

    product_response = api_client.patch(
        f"/api/v1/products/{product.pk}/",
        {"name": "Updated bag"},
        format="json",
    )
    item_response = api_client.patch(
        f"/api/v1/product-items/{item.pk}/",
        {"price": "15.50"},
        format="json",
    )
    product_delete_response = api_client.delete(f"/api/v1/products/{product.pk}/")
    item_delete_response = api_client.delete(f"/api/v1/product-items/{item.pk}/")
    product_put_response = api_client.put(
        f"/api/v1/products/{product.pk}/",
        {"name": "Replaced bag"},
        format="json",
    )
    item_put_response = api_client.put(
        f"/api/v1/product-items/{item.pk}/",
        {"name": "Replaced item"},
        format="json",
    )

    assert product_response.status_code == 200
    assert product_response.data["name"] == "Updated bag"
    assert item_response.status_code == 200
    assert item_response.data["price"] == "15.50"
    assert product_delete_response.status_code == 405
    assert item_delete_response.status_code == 405
    assert product_put_response.status_code == 405
    assert item_put_response.status_code == 405


@pytest.mark.django_db
def test_product_item_price_constraint_and_protected_relations(category, product):
    with transaction.atomic(), pytest.raises(IntegrityError):
        ProductItem.objects.create(
            product=product,
            sku="NEGATIVE-DB-PRICE",
            name="Invalid price",
            price=Decimal("-1.00"),
        )

    ProductItem.objects.create(
        product=product,
        sku="UNIQUE-DB-SKU",
        name="First item",
        price=Decimal("1.00"),
    )
    with transaction.atomic(), pytest.raises(IntegrityError):
        ProductItem.objects.create(
            product=product,
            sku="UNIQUE-DB-SKU",
            name="Duplicate item",
            price=Decimal("2.00"),
        )

    with pytest.raises(ProtectedError):
        category.delete()
