import secrets

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import CharField, Serializer, ValidationError
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.serializers import LoginSerializer, TokenPairSerializer
from users.models import User, UserRole
from users.serializers import UserSerializer


class AdminBootstrapSerializer(Serializer):
    password = CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value):
        try:
            validate_password(value, user=User(email="admin@admin.com"))
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from error
        return value


class AdminBootstrapView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        configured_token = settings.ADMIN_BOOTSTRAP_TOKEN
        provided_token = request.headers.get("X-Admin-Bootstrap-Token", "")
        if (
            len(configured_token) < 32
            or not provided_token
            or not secrets.compare_digest(provided_token, configured_token)
        ):
            raise NotFound

        admin_exists = User.objects.filter(
            Q(role=UserRole.ADMIN) | Q(is_staff=True) | Q(is_superuser=True)
        ).exists()
        if admin_exists:
            raise NotFound

        serializer = AdminBootstrapSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                if User.objects.filter(
                    Q(role=UserRole.ADMIN) | Q(is_staff=True) | Q(is_superuser=True)
                ).exists():
                    raise NotFound
                user = User.objects.create_superuser(
                    email="admin@admin.com",
                    password=serializer.validated_data["password"],
                )
        except IntegrityError as error:
            raise NotFound from error

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        request=LoginSerializer,
        responses={
            status.HTTP_200_OK: TokenPairSerializer,
            status.HTTP_401_UNAUTHORIZED: None,
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        refresh = RefreshToken.for_user(serializer.validated_data["user"])
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class RefreshView(TokenRefreshView):
    @extend_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Authentication"], responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)
