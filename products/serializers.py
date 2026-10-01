from rest_framework import serializers

from inventory.models import Inventory
from products.models import Product, ProductItem
from products.services import create_product_with_items


class ProductItemSummarySerializer(serializers.ModelSerializer):
    inventory_id = serializers.UUIDField(
        source="inventory.pk",
        read_only=True,
        allow_null=True,
    )
    stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductItem
        fields = ("id", "sku", "name", "price", "inventory_id", "stock")
        read_only_fields = fields

    def get_stock(self, product_item: ProductItem) -> int:
        try:
            return product_item.inventory.quantity
        except Inventory.DoesNotExist:
            return 0


class ProductSerializer(serializers.ModelSerializer):
    items = ProductItemSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "name",
            "description",
            "items",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("category", "name", "description", "is_active")

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value


class ProductItemCreateInputSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )
    stock = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate_sku(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("SKU cannot be blank.")
        if ProductItem.objects.filter(sku=value).exists():
            raise serializers.ValidationError("A product item with this SKU exists.")
        return value

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value


class ProductCreateSerializer(ProductWriteSerializer):
    items = ProductItemCreateInputSerializer(many=True, allow_empty=False)

    class Meta(ProductWriteSerializer.Meta):
        fields = (*ProductWriteSerializer.Meta.fields, "items")

    def validate_items(self, items: list[dict]) -> list[dict]:
        skus = [item["sku"] for item in items]
        if len(skus) != len(set(skus)):
            raise serializers.ValidationError("Each product item SKU must be unique.")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        return create_product_with_items(
            product_data=validated_data,
            items_data=items_data,
        )


class ProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = (
            "id",
            "product",
            "sku",
            "name",
            "price",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ProductItemWriteSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    class Meta:
        model = ProductItem
        fields = ("product", "sku", "name", "price", "is_active")

    def validate_sku(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("SKU cannot be blank.")
        return value

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value
