from rest_framework.permissions import BasePermission

from users.models import UserRole


class IsCustomer(BasePermission):
    message = "Customer role is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.CUSTOMER
        )
