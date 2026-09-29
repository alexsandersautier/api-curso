from rest_framework import serializers

from orders.models import Order, OrderItem
from products.models import ProductItem


class OrderProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductItem
        fields = ("id", "sku", "name")
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    product_item = OrderProductItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product_item", "quantity", "unit_price", "subtotal")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "customer",
            "status",
            "total",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("status",)

    def to_internal_value(self, data):
        unexpected_fields = set(data) - {"status"} if isinstance(data, dict) else set()
        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "Only the order status can be updated."
                    for field in unexpected_fields
                }
            )
        return super().to_internal_value(data)
