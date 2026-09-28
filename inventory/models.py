import uuid

from django.db import models

from products.models import ProductItem


class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_item = models.OneToOneField(
        ProductItem,
        on_delete=models.PROTECT,
        related_name="inventory",
    )
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.product_item.sku}: {self.quantity}"
