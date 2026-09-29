from django.urls import include, path
from rest_framework.routers import DefaultRouter

from carts.views import CartItemViewSet, CartMeView

router = DefaultRouter()
router.register("cart-items", CartItemViewSet, basename="cart-item")

urlpatterns = [
    path("carts/me/", CartMeView.as_view(), name="cart-me"),
    path("", include(router.urls)),
]
