from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from inventory.models import Inventory
from inventory.serializers import (
    InventoryAdminSerializer,
    InventoryAvailabilitySerializer,
    InventoryCreateSerializer,
    InventoryUpdateSerializer,
)
from users.models import UserRole
from users.permissions import IsApiAdmin


def inventory_read_schema(*, many: bool = False):
    return PolymorphicProxySerializer(
        component_name="InventoryRead",
        serializers=[InventoryAvailabilitySerializer, InventoryAdminSerializer],
        resource_type_field_name=None,
        many=many,
    )


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory"],
        responses={status.HTTP_200_OK: inventory_read_schema(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Inventory"],
        responses={status.HTTP_200_OK: inventory_read_schema()},
    ),
    create=extend_schema(
        tags=["Inventory"],
        request=InventoryCreateSerializer,
        responses={status.HTTP_201_CREATED: InventoryAdminSerializer},
    ),
    partial_update=extend_schema(
        tags=["Inventory"],
        request=InventoryUpdateSerializer,
        responses={status.HTTP_200_OK: InventoryAdminSerializer},
    ),
)
class InventoryViewSet(ModelViewSet):
    queryset = Inventory.objects.select_related(
        "product_item",
        "product_item__product",
    ).order_by("product_item__sku")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = Inventory.objects.select_related(
            "product_item",
            "product_item__product",
        )
        user = self.request.user
        if not user.is_authenticated or user.role != UserRole.ADMIN:
            queryset = queryset.filter(
                product_item__is_active=True,
                product_item__product__is_active=True,
            )
        return queryset.order_by("product_item__sku")

    def get_permissions(self):
        if self.action in {"list", "retrieve"} or self.request.method in {
            "HEAD",
            "OPTIONS",
        }:
            return [AllowAny()]
        return [IsApiAdmin()]

    def get_serializer_class(self):
        if self.action == "create":
            return InventoryCreateSerializer
        if self.action == "partial_update":
            return InventoryUpdateSerializer

        user = self.request.user
        if user.is_authenticated and user.role == UserRole.ADMIN:
            return InventoryAdminSerializer
        return InventoryAvailabilitySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory = serializer.save()
        return Response(
            InventoryAdminSerializer(inventory).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        inventory = self.get_object()
        serializer = self.get_serializer(inventory, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        inventory = serializer.save()
        return Response(InventoryAdminSerializer(inventory).data)
