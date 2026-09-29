from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from categories.models import Category
from customers.models import Customer
from inventory.models import Inventory
from products.models import Product, ProductItem
from users.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_user():
    user = User.objects.create_user(email="cart-customer@test.com", password="12345678")
    Customer.objects.create(user=user, name="Cart Customer", document="10000000001")
    return user


@pytest.fixture
def another_customer():
    user = User.objects.create_user(
        email="other-customer@test.com",
        password="12345678",
    )
    Customer.objects.create(user=user, name="Other Customer", document="10000000002")
    return user


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="cart-admin@test.com",
        password="12345678",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def product_item():
    category = Category.objects.create(name="Accessories", slug="cart-accessories")
    product = Product.objects.create(category=category, name="Bag")
    product_item = ProductItem.objects.create(
        product=product,
        sku="CART-BAG-001",
        name="Blue bag",
        price=Decimal("25.00"),
    )
    Inventory.objects.create(product_item=product_item, quantity=4)
    return product_item


def authenticate(api_client, user):
    api_client.force_authenticate(user=user)


@pytest.mark.django_db
def test_customer_creates_and_reads_only_one_cart(api_client, customer_user):
    authenticate(api_client, customer_user)

    create_response = api_client.post("/api/v1/carts/me/", {}, format="json")
    read_response = api_client.get("/api/v1/carts/me/")
    duplicate_response = api_client.post("/api/v1/carts/me/", {}, format="json")

    assert create_response.status_code == 201
    assert read_response.status_code == 200
    assert read_response.data["id"] == create_response.data["id"]
    assert read_response.data["items"] == []
    assert Decimal(str(read_response.data["total"])) == Decimal("0.00")
    assert duplicate_response.status_code == 400


@pytest.mark.django_db
def test_cart_requires_customer_role_and_profile(api_client, customer_user, admin_user):
    unauthenticated_response = api_client.get("/api/v1/carts/me/")
    authenticate(api_client, admin_user)
    admin_response = api_client.get("/api/v1/carts/me/")

    assert unauthenticated_response.status_code == 401
    assert admin_response.status_code == 403

    customer_user.customer.delete()
    customer_user.refresh_from_db()
    authenticate(api_client, customer_user)
    no_profile_response = api_client.post("/api/v1/carts/me/", {}, format="json")
    assert no_profile_response.status_code == 404


@pytest.mark.django_db
def test_customer_manages_cart_items_and_current_totals(
    api_client, customer_user, product_item
):
    authenticate(api_client, customer_user)
    api_client.post("/api/v1/carts/me/", {}, format="json")

    create_response = api_client.post(
        "/api/v1/cart-items/",
        {"product_item": str(product_item.pk), "quantity": 2},
        format="json",
    )
    list_response = api_client.get("/api/v1/cart-items/")
    cart_response = api_client.get("/api/v1/carts/me/")
    update_response = api_client.patch(
        f"/api/v1/cart-items/{create_response.data['id']}/",
        {"quantity": 3},
        format="json",
    )

    assert create_response.status_code == 201
    assert Decimal(str(create_response.data["subtotal"])) == Decimal("50.00")
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert Decimal(str(cart_response.data["total"])) == Decimal("50.00")
    assert update_response.status_code == 200
    assert Decimal(str(update_response.data["subtotal"])) == Decimal("75.00")

    delete_response = api_client.delete(
        f"/api/v1/cart-items/{create_response.data['id']}/"
    )
    assert delete_response.status_code == 204
    assert api_client.get("/api/v1/cart-items/").data["count"] == 0


@pytest.mark.django_db
def test_cart_item_is_private_to_its_customer(
    api_client, customer_user, another_customer, product_item
):
    authenticate(api_client, customer_user)
    api_client.post("/api/v1/carts/me/", {}, format="json")
    create_response = api_client.post(
        "/api/v1/cart-items/",
        {"product_item": str(product_item.pk), "quantity": 1},
        format="json",
    )

    authenticate(api_client, another_customer)
    other_cart = api_client.get("/api/v1/carts/me/")
    other_item = api_client.patch(
        f"/api/v1/cart-items/{create_response.data['id']}/",
        {"quantity": 2},
        format="json",
    )

    assert other_cart.status_code == 404
    assert other_item.status_code == 404


@pytest.mark.django_db
def test_cart_item_rejects_duplicate_unknown_fields_and_invalid_quantity(
    api_client, customer_user, product_item
):
    authenticate(api_client, customer_user)
    api_client.post("/api/v1/carts/me/", {}, format="json")
    payload = {"product_item": str(product_item.pk), "quantity": 1}
    first_response = api_client.post("/api/v1/cart-items/", payload, format="json")
    duplicate_response = api_client.post("/api/v1/cart-items/", payload, format="json")
    zero_response = api_client.post(
        "/api/v1/cart-items/", {**payload, "quantity": 0}, format="json"
    )
    extra_field_response = api_client.post(
        "/api/v1/cart-items/", {**payload, "cart": "other"}, format="json"
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 400
    assert zero_response.status_code == 400
    assert extra_field_response.status_code == 400


@pytest.mark.django_db
def test_cart_item_rejects_inactive_and_insufficient_stock(
    api_client, customer_user, product_item
):
    authenticate(api_client, customer_user)
    api_client.post("/api/v1/carts/me/", {}, format="json")
    endpoint = "/api/v1/cart-items/"
    too_many_response = api_client.post(
        endpoint,
        {"product_item": str(product_item.pk), "quantity": 5},
        format="json",
    )
    product_item.is_active = False
    product_item.save(update_fields=["is_active"])
    inactive_response = api_client.post(
        endpoint,
        {"product_item": str(product_item.pk), "quantity": 1},
        format="json",
    )

    assert too_many_response.status_code == 400
    assert inactive_response.status_code == 400


@pytest.mark.django_db
def test_cart_item_database_constraints_require_unique_positive_items(
    customer_user, product_item
):
    from carts.models import Cart, CartItem

    cart = Cart.objects.create(customer=customer_user.customer)
    CartItem.objects.create(cart=cart, product_item=product_item, quantity=1)

    with transaction.atomic(), pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, product_item=product_item, quantity=2)

    with transaction.atomic(), pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, product_item=product_item, quantity=0)
