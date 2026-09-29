from decimal import Decimal

from django.db import transaction

from carts.models import Cart, CartItem
from customers.models import Customer
from inventory.models import Inventory
from orders.models import Order, OrderItem
from products.models import Product, ProductItem


class CheckoutError(Exception):
    """Base exception for a checkout that cannot complete."""


class CartNotFoundError(CheckoutError):
    pass


class EmptyCartError(CheckoutError):
    pass


class ProductUnavailableError(CheckoutError):
    pass


class InventoryMissingError(CheckoutError):
    pass


class InsufficientStockError(CheckoutError):
    pass


@transaction.atomic
def create_order_from_cart(customer: Customer) -> Order:
    cart = Cart.objects.select_for_update().filter(customer=customer).first()
    if cart is None:
        raise CartNotFoundError("Customer does not have a cart.")

    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(cart=cart)
        .order_by("product_item_id")
    )
    if not cart_items:
        raise EmptyCartError("Cannot create an order from an empty cart.")

    product_item_ids = [cart_item.product_item_id for cart_item in cart_items]
    product_items = {
        product_item.pk: product_item
        for product_item in ProductItem.objects.select_for_update()
        .filter(pk__in=product_item_ids)
        .order_by("pk")
    }
    product_ids = [product_item.product_id for product_item in product_items.values()]
    products = {
        product.pk: product
        for product in Product.objects.select_for_update()
        .filter(pk__in=product_ids)
        .order_by("pk")
    }
    inventories = {
        inventory.product_item_id: inventory
        for inventory in Inventory.objects.select_for_update()
        .filter(product_item_id__in=product_item_ids)
        .order_by("product_item_id")
    }

    order_lines = []
    for cart_item in cart_items:
        product_item = product_items[cart_item.product_item_id]
        product = products[product_item.product_id]
        if not product_item.is_active or not product.is_active:
            raise ProductUnavailableError(
                f"Product item {product_item.sku} is no longer available."
            )

        inventory = inventories.get(product_item.pk)
        if inventory is None:
            raise InventoryMissingError(
                f"Product item {product_item.sku} has no inventory record."
            )
        if inventory.quantity < cart_item.quantity:
            raise InsufficientStockError(
                f"Insufficient stock for product item {product_item.sku}."
            )

        unit_price = product_item.price
        subtotal = unit_price * cart_item.quantity
        order_lines.append(
            (cart_item, product_item, inventory, unit_price, subtotal)
        )

    total = sum((line[4] for line in order_lines), Decimal("0.00"))
    order = Order.objects.create(customer=customer, total=total)
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product_item=product_item,
                quantity=cart_item.quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )
            for cart_item, product_item, _, unit_price, subtotal in order_lines
        ]
    )

    for cart_item, _, inventory, _, _ in order_lines:
        inventory.quantity -= cart_item.quantity
        inventory.save(update_fields=("quantity", "updated_at"))

    CartItem.objects.filter(pk__in=[item.pk for item in cart_items]).delete()
    return order
