from rest_framework import serializers

from customers.models import Customer


class CustomerFieldsMixin:
    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_phone(self, value):
        return value.strip()

    def validate_document(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Document cannot be blank.")
        return value


class CustomerCreateSerializer(CustomerFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("name", "phone", "document")

    def to_internal_value(self, data):
        unexpected_fields = set(data.keys()) - {"name", "phone", "document"}
        if unexpected_fields:
            raise serializers.ValidationError(
                {field: "This field cannot be set." for field in unexpected_fields}
            )
        return super().to_internal_value(data)


class CustomerUpdateSerializer(CustomerFieldsMixin, serializers.ModelSerializer):
    allowed_fields = {"name", "phone", "document"}

    class Meta:
        model = Customer
        fields = ("name", "phone", "document")

    def to_internal_value(self, data):
        unexpected_fields = set(data.keys()) - self.allowed_fields
        if unexpected_fields:
            raise serializers.ValidationError(
                {field: "This field cannot be updated." for field in unexpected_fields}
            )
        return super().to_internal_value(data)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "user", "name", "phone", "document", "created_at", "updated_at")
        read_only_fields = fields
