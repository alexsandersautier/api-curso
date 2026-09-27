from rest_framework import serializers

from products.models import Product, ProductItem


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "name",
            "description",
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
