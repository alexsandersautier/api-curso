from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from products.models import Product, ProductItem
from products.serializers import (
    ProductCreateSerializer,
    ProductItemSerializer,
    ProductItemWriteSerializer,
    ProductSerializer,
    ProductWriteSerializer,
)
from users.models import UserRole
from users.permissions import IsApiAdmin


@extend_schema_view(
    list=extend_schema(tags=["Products"], responses=ProductSerializer),
    retrieve=extend_schema(tags=["Products"], responses=ProductSerializer),
    create=extend_schema(
        tags=["Products"],
        request=ProductCreateSerializer,
        responses={status.HTTP_201_CREATED: ProductSerializer},
    ),
    partial_update=extend_schema(
        tags=["Products"],
        request=ProductWriteSerializer,
        responses={status.HTTP_200_OK: ProductSerializer},
    ),
)
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category").order_by("name")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        item_queryset = ProductItem.objects.select_related("inventory")
        user = self.request.user
        if not user.is_authenticated or user.role != UserRole.ADMIN:
            item_queryset = item_queryset.filter(is_active=True)
            queryset = Product.objects.filter(is_active=True)
        else:
            queryset = Product.objects.all()
        return (
            queryset.select_related("category")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=item_queryset.order_by("name"),
                )
            )
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ProductCreateSerializer
        if self.action == "partial_update":
            return ProductWriteSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"} or self.request.method in {
            "HEAD",
            "OPTIONS",
        }:
            return [AllowAny()]
        return [IsApiAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            ProductSerializer(product).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductSerializer(product).data)


@extend_schema_view(
    list=extend_schema(tags=["Product items"], responses=ProductItemSerializer),
    retrieve=extend_schema(tags=["Product items"], responses=ProductItemSerializer),
    create=extend_schema(
        tags=["Product items"],
        request=ProductItemWriteSerializer,
        responses={status.HTTP_201_CREATED: ProductItemSerializer},
    ),
    partial_update=extend_schema(
        tags=["Product items"],
        request=ProductItemWriteSerializer,
        responses={status.HTTP_200_OK: ProductItemSerializer},
    ),
)
class ProductItemViewSet(ModelViewSet):
    queryset = ProductItem.objects.select_related("product").order_by("sku")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = ProductItem.objects.select_related("product")
        user = self.request.user
        if not user.is_authenticated or user.role != UserRole.ADMIN:
            queryset = queryset.filter(is_active=True, product__is_active=True)
        return queryset.order_by("sku")

    def get_serializer_class(self):
        if self.action in {"create", "partial_update"}:
            return ProductItemWriteSerializer
        return ProductItemSerializer

    def get_permissions(self):
        if self.action in {"list", "retrieve"} or self.request.method in {
            "HEAD",
            "OPTIONS",
        }:
            return [AllowAny()]
        return [IsApiAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_item = serializer.save()
        return Response(
            ProductItemSerializer(product_item).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        product_item = self.get_object()
        serializer = self.get_serializer(
            product_item,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        product_item = serializer.save()
        return Response(ProductItemSerializer(product_item).data)
