from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from users.models import User
from users.permissions import IsApiAdmin
from users.serializers import UserCreateSerializer, UserSerializer, UserUpdateSerializer


@extend_schema_view(
    list=extend_schema(tags=["Users"], responses=UserSerializer),
    retrieve=extend_schema(tags=["Users"], responses=UserSerializer),
    create=extend_schema(
        tags=["Users"],
        request=UserCreateSerializer,
        responses={status.HTTP_201_CREATED: UserSerializer},
    ),
    partial_update=extend_schema(
        tags=["Users"],
        request=UserUpdateSerializer,
        responses={status.HTTP_200_OK: UserSerializer},
    ),
)
class UserViewSet(ModelViewSet):
    queryset = User.objects.order_by("created_at")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "partial_update":
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsApiAdmin()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(UserSerializer(user).data)
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)
