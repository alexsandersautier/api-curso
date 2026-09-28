from rest_framework import serializers

from inventory.models import Inventory
from products.models import ProductItem


class InventoryAvailabilitySerializer(serializers.ModelSerializer):
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = ("id", "product_item", "in_stock", "created_at", "updated_at")
        read_only_fields = fields

    def get_in_stock(self, inventory: Inventory) -> bool:
        return inventory.quantity > 0


class InventoryAdminSerializer(serializers.ModelSerializer):
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = (
            "id",
            "product_item",
            "quantity",
            "in_stock",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_in_stock(self, inventory: Inventory) -> bool:
        return inventory.quantity > 0


class InventoryCreateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=0)

    class Meta:
        model = Inventory
        fields = ("product_item", "quantity")

    def validate_product_item(self, product_item: ProductItem) -> ProductItem:
        if Inventory.objects.filter(product_item=product_item).exists():
            raise serializers.ValidationError(
                "Inventory already exists for this product item."
            )
        return product_item


class InventoryUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=0)

    class Meta:
        model = Inventory
        fields = ("quantity",)

    def to_internal_value(self, data):
        unexpected_fields = set(data.keys()) - {"quantity"}
        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "Only quantity can be changed through this endpoint."
                    for field in unexpected_fields
                }
            )
        return super().to_internal_value(data)
