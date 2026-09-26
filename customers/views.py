from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from customers.models import Customer
from customers.permissions import IsCustomer
from customers.serializers import (
    CustomerCreateSerializer,
    CustomerSerializer,
    CustomerUpdateSerializer,
)
from users.permissions import IsApiAdmin


class CustomerMeView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_customer(self, user):
        try:
            return user.customer
        except Customer.DoesNotExist as error:
            raise NotFound("Customer profile does not exist.") from error

    @extend_schema(tags=["Customers"], responses=CustomerSerializer)
    def get(self, request):
        return Response(CustomerSerializer(self.get_customer(request.user)).data)

    @extend_schema(
        tags=["Customers"],
        request=CustomerCreateSerializer,
        responses={status.HTTP_201_CREATED: CustomerSerializer},
    )
    def post(self, request):
        if Customer.objects.filter(user=request.user).exists():
            raise ValidationError({"detail": "Customer profile already exists."})
        serializer = CustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save(user=request.user)
        return Response(
            CustomerSerializer(customer).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Customers"],
        request=CustomerUpdateSerializer,
        responses={status.HTTP_200_OK: CustomerSerializer},
    )
    def patch(self, request):
        customer = self.get_customer(request.user)
        serializer = CustomerUpdateSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response(CustomerSerializer(customer).data)


@extend_schema_view(
    list=extend_schema(tags=["Customers"], responses=CustomerSerializer),
    retrieve=extend_schema(tags=["Customers"], responses=CustomerSerializer),
    partial_update=extend_schema(
        tags=["Customers"],
        request=CustomerUpdateSerializer,
        responses={status.HTTP_200_OK: CustomerSerializer},
    ),
)
class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("user").order_by("created_at")
    permission_classes = [IsApiAdmin]
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "partial_update":
            return CustomerUpdateSerializer
        return CustomerSerializer

    def update(self, request, *args, **kwargs):
        customer = self.get_object()
        serializer = self.get_serializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return Response(CustomerSerializer(customer).data)
