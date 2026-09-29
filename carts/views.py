from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from carts.models import Cart, CartItem
from carts.serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
)
from customers.models import Customer
from customers.permissions import IsCustomer

User = get_user_model()


def get_customer(user: User) -> Customer:
    try:
        return user.customer
    except Customer.DoesNotExist as error:
        raise NotFound("Customer profile does not exist.") from error


def get_cart(user: User) -> Cart:
    try:
        return get_customer(user).cart
    except Cart.DoesNotExist as error:
        raise NotFound("Cart does not exist.") from error


class CartMeView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    @extend_schema(tags=["Carts"], responses=CartSerializer)
    def get(self, request):
        cart = get_object_or_404(
            Cart.objects.prefetch_related(
                Prefetch(
                    "items",
                    queryset=CartItem.objects.select_related("product_item"),
                )
            ),
            customer=get_customer(request.user),
        )
        return Response(CartSerializer(cart).data)

    @extend_schema(
        tags=["Carts"],
        request=None,
        responses={status.HTTP_201_CREATED: CartSerializer},
    )
    def post(self, request):
        customer = get_customer(request.user)
        cart, created = Cart.objects.get_or_create(customer=customer)
        if not created:
            raise ValidationError({"detail": "Customer already has a cart."})
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(tags=["Cart Items"], responses=CartItemSerializer(many=True)),
    retrieve=extend_schema(tags=["Cart Items"], responses=CartItemSerializer),
    create=extend_schema(
        tags=["Cart Items"],
        request=CartItemCreateSerializer,
        responses={status.HTTP_201_CREATED: CartItemSerializer},
    ),
    partial_update=extend_schema(
        tags=["Cart Items"],
        request=CartItemUpdateSerializer,
        responses={status.HTTP_200_OK: CartItemSerializer},
    ),
)
class CartItemViewSet(ModelViewSet):
    queryset = CartItem.objects.select_related("product_item").order_by("created_at")
    permission_classes = [IsAuthenticated, IsCustomer]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return (
            CartItem.objects.filter(cart__customer__user=self.request.user)
            .select_related("product_item")
            .order_by("created_at")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return CartItemCreateSerializer
        if self.action == "partial_update":
            return CartItemUpdateSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "create":
            context["cart"] = get_cart(self.request.user)
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save(cart=get_cart(request.user))
        return Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        cart_item = self.get_object()
        serializer = self.get_serializer(cart_item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()
        return Response(CartItemSerializer(cart_item).data)
