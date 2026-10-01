from typing import Any

from django.db import transaction

from inventory.models import Inventory
from products.models import Product, ProductItem


@transaction.atomic
def create_product_with_items(
    *,
    product_data: dict[str, Any],
    items_data: list[dict[str, Any]],
) -> Product:
    product = Product.objects.create(**product_data)

    for item_data in items_data:
        item_fields = {
            field: value for field, value in item_data.items() if field != "stock"
        }
        product_item = ProductItem.objects.create(product=product, **item_fields)
        Inventory.objects.create(
            product_item=product_item,
            quantity=item_data.get("stock", 0),
        )

    return product
