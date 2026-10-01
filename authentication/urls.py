from django.urls import path

from authentication.views import (
    AdminBootstrapView,
    CurrentUserView,
    LoginView,
    RefreshView,
)

urlpatterns = [
    path("bootstrap-admin/", AdminBootstrapView.as_view(), name="bootstrap-admin"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("me/", CurrentUserView.as_view(), name="me"),
]
