from django.contrib import admin

from inventory.models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product_item", "quantity", "updated_at")
    search_fields = (
        "product_item__sku",
        "product_item__name",
        "product_item__product__name",
    )
    list_select_related = ("product_item", "product_item__product")
