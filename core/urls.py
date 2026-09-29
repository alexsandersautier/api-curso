from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.api import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/", include("carts.urls")),
    path("api/v1/", include("categories.urls")),
    path("api/v1/", include("customers.urls")),
    path("api/v1/", include("inventory.urls")),
    path("api/v1/", include("orders.urls")),
    path("api/v1/", include("products.urls")),
    path("api/v1/", include("users.urls")),
]
