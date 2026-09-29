from decimal import Decimal

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from carts.models import Cart, CartItem
from inventory.models import Inventory
from products.models import ProductItem


class CartProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = ("id", "sku", "name", "price")
        read_only_fields = fields


class CartItemSerializer(serializers.ModelSerializer):
    product_item = CartProductItemSerializer(read_only=True)
    unit_price = serializers.DecimalField(
        source="product_item.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            "id",
            "product_item",
            "quantity",
            "unit_price",
            "subtotal",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_subtotal(self, cart_item: CartItem) -> Decimal:
        return cart_item.product_item.price * cart_item.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "items", "total", "created_at", "updated_at")
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_total(self, cart: Cart) -> Decimal:
        return sum(
            (
                item.product_item.price * item.quantity
                for item in cart.items.all()
            ),
            Decimal("0.00"),
        )


class CartItemCreateSerializer(serializers.ModelSerializer):
    product_item = serializers.PrimaryKeyRelatedField(
        queryset=ProductItem.objects.filter(
            is_active=True,
            product__is_active=True,
        )
    )
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
        fields = ("product_item", "quantity")

    def to_internal_value(self, data):
        unexpected_fields = set(data.keys()) - {"product_item", "quantity"}
        if unexpected_fields:
            raise serializers.ValidationError(
                {field: "This field cannot be set." for field in unexpected_fields}
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        cart = self.context["cart"]
        product_item = attrs["product_item"]
        if CartItem.objects.filter(cart=cart, product_item=product_item).exists():
            raise serializers.ValidationError(
                {"product_item": "This product item is already in the cart."}
            )
        self.validate_stock(product_item, attrs["quantity"])
        return attrs

    @staticmethod
    def validate_stock(product_item: ProductItem, quantity: int) -> None:
        try:
            inventory = product_item.inventory
        except Inventory.DoesNotExist as error:
            raise serializers.ValidationError(
                {"product_item": "This product item has no inventory record."}
            ) from error
        if inventory.quantity < quantity:
            raise serializers.ValidationError(
                {"quantity": "Requested quantity exceeds available stock."}
            )


class CartItemUpdateSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = CartItem
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

    def validate_quantity(self, quantity: int) -> int:
        CartItemCreateSerializer.validate_stock(self.instance.product_item, quantity)
        return quantity
