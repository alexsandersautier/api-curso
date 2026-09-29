from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from customers.models import Customer
from customers.permissions import IsCustomer
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from orders.services import (
    CartNotFoundError,
    EmptyCartError,
    InsufficientStockError,
    InventoryMissingError,
    ProductUnavailableError,
    create_order_from_cart,
)

User = get_user_model()


class CheckoutConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Cart contents conflict with current product availability."
    default_code = "checkout_conflict"


def get_customer(user: User) -> Customer:
    try:
        return user.customer
    except Customer.DoesNotExist as error:
        raise NotFound("Customer profile does not exist.") from error


@extend_schema_view(
    list=extend_schema(tags=["Orders"], responses=OrderSerializer(many=True)),
    retrieve=extend_schema(tags=["Orders"], responses=OrderSerializer),
    create=extend_schema(
        tags=["Orders"],
        request=None,
        responses={
            status.HTTP_201_CREATED: OrderSerializer,
            status.HTTP_400_BAD_REQUEST: None,
            status.HTTP_404_NOT_FOUND: None,
            status.HTTP_409_CONFLICT: None,
        },
    ),
)
class OrderViewSet(ModelViewSet):
    queryset = Order.objects.select_related("customer").order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return (
            Order.objects.filter(customer__user=self.request.user)
            .select_related("customer")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product_item"),
                )
            )
            .order_by("-created_at")
        )

    def create(self, request, *args, **kwargs):
        if request.data:
            raise ValidationError(
                {
                    "detail": "Orders use the current cart; no fields are accepted."
                }
            )

        customer = get_customer(request.user)
        try:
            order = create_order_from_cart(customer)
        except CartNotFoundError as error:
            raise NotFound(str(error)) from error
        except EmptyCartError as error:
            raise ValidationError({"detail": str(error)}) from error
        except (
            ProductUnavailableError,
            InventoryMissingError,
            InsufficientStockError,
        ) as error:
            raise CheckoutConflict(str(error)) from error

        order = self.get_queryset().get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
