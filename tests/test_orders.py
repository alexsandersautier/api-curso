import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from carts.models import Cart, CartItem
from categories.models import Category
from customers.models import Customer
from inventory.models import Inventory
from orders.models import Order
from products.models import Product, ProductItem
from users.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_user():
    user = User.objects.create_user(
        email="order-customer@test.com",
        password="12345678",
    )
    Customer.objects.create(user=user, name="Order Customer", document="20000000001")
    return user


@pytest.fixture
def another_customer():
    user = User.objects.create_user(
        email="other-order-customer@test.com",
        password="12345678",
    )
    Customer.objects.create(user=user, name="Other Customer", document="20000000002")
    return user


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="order-admin@test.com",
        password="12345678",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def product_items():
    category = Category.objects.create(name="Order Products", slug="order-products")
    product = Product.objects.create(category=category, name="Course Kit")
    first_item = ProductItem.objects.create(
        product=product,
        sku="ORDER-KIT-001",
        name="Main kit",
        price=Decimal("25.00"),
    )
    second_item = ProductItem.objects.create(
        product=product,
        sku="ORDER-KIT-002",
        name="Extra kit",
        price=Decimal("10.50"),
    )
    first_inventory = Inventory.objects.create(product_item=first_item, quantity=5)
    second_inventory = Inventory.objects.create(product_item=second_item, quantity=5)
    return first_item, second_item, first_inventory, second_inventory


@pytest.fixture
def cart(customer_user):
    return Cart.objects.create(customer=customer_user.customer)


def authenticate(api_client, user):
    api_client.force_authenticate(user=user)


@pytest.mark.django_db
def test_checkout_creates_order_snapshots_prices_decrements_stock_and_clears_cart(
    api_client, customer_user, cart, product_items
):
    first_item, second_item, first_inventory, second_inventory = product_items
    CartItem.objects.create(cart=cart, product_item=first_item, quantity=2)
    CartItem.objects.create(cart=cart, product_item=second_item, quantity=1)
    authenticate(api_client, customer_user)

    response = api_client.post("/api/v1/orders/", {}, format="json")

    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert Decimal(str(response.data["total"])) == Decimal("60.50")
    assert len(response.data["items"]) == 2
    first_order_item = next(
        item
        for item in response.data["items"]
        if uuid.UUID(str(item["product_item"]["id"])) == first_item.pk
    )
    assert Decimal(str(first_order_item["unit_price"])) == Decimal("25.00")
    assert Decimal(str(first_order_item["subtotal"])) == Decimal("50.00")

    first_inventory.refresh_from_db()
    second_inventory.refresh_from_db()
    assert first_inventory.quantity == 3
    assert second_inventory.quantity == 4
    assert cart.items.count() == 0


@pytest.mark.django_db
def test_checkout_keeps_historical_price_after_catalog_price_changes(
    api_client, customer_user, cart, product_items
):
    first_item, _, _, _ = product_items
    CartItem.objects.create(cart=cart, product_item=first_item, quantity=2)
    authenticate(api_client, customer_user)

    response = api_client.post("/api/v1/orders/", {}, format="json")
    first_item.price = Decimal("35.00")
    first_item.save(update_fields=["price"])
    order_detail = api_client.get(f"/api/v1/orders/{response.data['id']}/")

    assert response.status_code == 201
    assert Decimal(str(order_detail.data["items"][0]["unit_price"])) == Decimal("25.00")
    assert Decimal(str(order_detail.data["items"][0]["subtotal"])) == Decimal("50.00")
    assert Decimal(str(order_detail.data["total"])) == Decimal("50.00")


@pytest.mark.django_db
def test_checkout_rejects_missing_and_empty_cart(api_client, customer_user):
    authenticate(api_client, customer_user)
    missing_cart_response = api_client.post("/api/v1/orders/", {}, format="json")
    Cart.objects.create(customer=customer_user.customer)
    empty_cart_response = api_client.post("/api/v1/orders/", {}, format="json")

    assert missing_cart_response.status_code == 404
    assert empty_cart_response.status_code == 400


@pytest.mark.django_db
def test_checkout_rolls_back_all_changes_when_stock_is_insufficient(
    api_client, customer_user, cart, product_items
):
    first_item, second_item, first_inventory, second_inventory = product_items
    CartItem.objects.create(cart=cart, product_item=first_item, quantity=2)
    CartItem.objects.create(cart=cart, product_item=second_item, quantity=2)
    second_inventory.quantity = 1
    second_inventory.save(update_fields=["quantity"])
    authenticate(api_client, customer_user)

    response = api_client.post("/api/v1/orders/", {}, format="json")

    first_inventory.refresh_from_db()
    second_inventory.refresh_from_db()
    assert response.status_code == 409
    assert first_inventory.quantity == 5
    assert second_inventory.quantity == 1
    assert cart.items.count() == 2
    assert not customer_user.customer.orders.exists()


@pytest.mark.django_db
def test_checkout_rejects_inactive_catalog_items_without_side_effects(
    api_client, customer_user, cart, product_items
):
    first_item, _, first_inventory, _ = product_items
    CartItem.objects.create(cart=cart, product_item=first_item, quantity=1)
    first_item.product.is_active = False
    first_item.product.save(update_fields=["is_active"])
    authenticate(api_client, customer_user)

    response = api_client.post("/api/v1/orders/", {}, format="json")

    first_inventory.refresh_from_db()
    assert response.status_code == 409
    assert first_inventory.quantity == 5
    assert cart.items.count() == 1


@pytest.mark.django_db
def test_orders_require_customer_authentication_and_are_customer_scoped(
    api_client, customer_user, another_customer, admin_user, cart, product_items
):
    first_item, _, _, _ = product_items
    CartItem.objects.create(cart=cart, product_item=first_item, quantity=1)
    other_order = Order.objects.create(
        customer=another_customer.customer,
        total=Decimal("12.00"),
    )
    anonymous_response = api_client.get("/api/v1/orders/")

    authenticate(api_client, customer_user)
    create_response = api_client.post("/api/v1/orders/", {}, format="json")
    own_orders_response = api_client.get("/api/v1/orders/")
    own_detail_response = api_client.get(
        f"/api/v1/orders/{create_response.data['id']}/"
    )
    customer_update_response = api_client.patch(
        f"/api/v1/orders/{create_response.data['id']}/",
        {"status": "confirmed"},
        format="json",
    )

    authenticate(api_client, another_customer)
    other_orders_response = api_client.get("/api/v1/orders/")
    other_detail_response = api_client.get(
        f"/api/v1/orders/{create_response.data['id']}/"
    )
    authenticate(api_client, admin_user)
    admin_response = api_client.get("/api/v1/orders/")
    admin_detail_response = api_client.get(f"/api/v1/orders/{other_order.pk}/")
    admin_update_response = api_client.patch(
        f"/api/v1/orders/{other_order.pk}/",
        {"status": "confirmed"},
        format="json",
    )

    assert anonymous_response.status_code == 401
    assert create_response.status_code == 201
    assert own_orders_response.data["count"] == 1
    assert own_detail_response.status_code == 200
    assert customer_update_response.status_code == 403
    assert other_orders_response.data["count"] == 1
    assert other_detail_response.status_code == 404
    assert admin_response.status_code == 200
    assert admin_response.data["count"] == 2
    assert admin_detail_response.status_code == 200
    assert admin_detail_response.data["id"] == str(other_order.pk)
    assert admin_update_response.status_code == 200
    assert admin_update_response.data["status"] == "confirmed"


@pytest.mark.django_db
def test_admin_order_update_accepts_only_a_valid_status(
    api_client, admin_user, customer_user
):
    order = Order.objects.create(
        customer=customer_user.customer,
        total=Decimal("12.00"),
    )
    authenticate(api_client, admin_user)

    invalid_status_response = api_client.patch(
        f"/api/v1/orders/{order.pk}/",
        {"status": "shipped"},
        format="json",
    )
    protected_fields_response = api_client.patch(
        f"/api/v1/orders/{order.pk}/",
        {"status": "confirmed", "total": "0.00"},
        format="json",
    )

    order.refresh_from_db()
    assert invalid_status_response.status_code == 400
    assert protected_fields_response.status_code == 400
    assert order.status == "pending"


@pytest.mark.django_db
def test_checkout_rejects_payload_and_full_order_updates(
    api_client, customer_user, cart
):
    authenticate(api_client, customer_user)
    payload_response = api_client.post(
        "/api/v1/orders/",
        {"status": "completed", "total": "0.00"},
        format="json",
    )
    assert payload_response.status_code == 400

    from orders.models import Order

    order = Order.objects.create(customer=customer_user.customer, total=Decimal("0.00"))
    put_response = api_client.put(
        f"/api/v1/orders/{order.pk}/",
        {"status": "completed"},
        format="json",
    )
    delete_response = api_client.delete(f"/api/v1/orders/{order.pk}/")

    assert put_response.status_code == 405
    assert delete_response.status_code == 405


@pytest.mark.django_db
def test_order_item_constraints_require_unique_positive_quantities(
    customer_user, product_items
):
    from orders.models import Order, OrderItem

    first_item, _, _, _ = product_items
    order = Order.objects.create(customer=customer_user.customer, total=Decimal("2.00"))
    OrderItem.objects.create(
        order=order,
        product_item=first_item,
        quantity=1,
        unit_price=Decimal("2.00"),
        subtotal=Decimal("2.00"),
    )

    with transaction.atomic(), pytest.raises(IntegrityError):
        OrderItem.objects.create(
            order=order,
            product_item=first_item,
            quantity=1,
            unit_price=Decimal("2.00"),
            subtotal=Decimal("2.00"),
        )

    with transaction.atomic(), pytest.raises(IntegrityError):
        OrderItem.objects.create(
            order=order,
            product_item=first_item,
            quantity=0,
            unit_price=Decimal("2.00"),
            subtotal=Decimal("0.00"),
        )
