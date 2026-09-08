from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class NormalizedEmailMixin:
    def validate_email(self, value: str) -> str:
        normalized_email = value.strip().lower()
        users = User.objects.filter(email=normalized_email)
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_email


class UserCreateSerializer(NormalizedEmailMixin, serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=8, trim_whitespace=False
    )

    class Meta:
        model = User
        fields = ("email", "password", "role")
        extra_kwargs = {"role": {"required": False}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(NormalizedEmailMixin, serializers.ModelSerializer):
    allowed_fields = {"email", "role", "is_active"}

    class Meta:
        model = User
        fields = ("email", "role", "is_active")

    def to_internal_value(self, data):
        unexpected_fields = set(data.keys()) - self.allowed_fields
        if unexpected_fields:
            raise serializers.ValidationError(
                {
                    field: "This field cannot be updated through this endpoint."
                    for field in unexpected_fields
                }
            )
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "is_active", "created_at", "updated_at")
        read_only_fields = fields
