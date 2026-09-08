from django.urls import path

from authentication.views import CurrentUserView, LoginView, RefreshView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("me/", CurrentUserView.as_view(), name="me"),
]
