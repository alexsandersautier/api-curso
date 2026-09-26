from rest_framework import serializers

from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "is_active", "created_at", "updated_at")
        read_only_fields = fields


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug", "is_active")

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_slug(self, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Slug cannot be blank.")
        return value
