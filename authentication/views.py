from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.serializers import LoginSerializer, TokenPairSerializer
from users.serializers import UserSerializer


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
