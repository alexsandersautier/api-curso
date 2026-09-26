from django.urls import path
from rest_framework.routers import DefaultRouter

from customers.views import CustomerMeView, CustomerViewSet

router = DefaultRouter()
router.register("customers", CustomerViewSet, basename="customer")

urlpatterns = [
    path("customers/me/", CustomerMeView.as_view(), name="customer-me"),
] + router.urls
