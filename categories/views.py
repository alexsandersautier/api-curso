from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from categories.models import Category
from categories.serializers import CategorySerializer, CategoryWriteSerializer
from users.models import UserRole
from users.permissions import IsApiAdmin


@extend_schema_view(
    list=extend_schema(tags=["Categories"], responses=CategorySerializer),
    retrieve=extend_schema(tags=["Categories"], responses=CategorySerializer),
    create=extend_schema(
        tags=["Categories"],
        request=CategoryWriteSerializer,
        responses={status.HTTP_201_CREATED: CategorySerializer},
    ),
    partial_update=extend_schema(
        tags=["Categories"],
        request=CategoryWriteSerializer,
        responses={status.HTTP_200_OK: CategorySerializer},
    ),
)
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.order_by("name")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == UserRole.ADMIN:
            return Category.objects.order_by("name")
        return Category.objects.filter(is_active=True).order_by("name")

    def get_serializer_class(self):
        if self.action in {"create", "partial_update"}:
            return CategoryWriteSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [IsApiAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(
            CategorySerializer(category).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(CategorySerializer(category).data)
