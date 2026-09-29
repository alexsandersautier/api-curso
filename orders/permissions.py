from rest_framework.permissions import BasePermission

from users.models import UserRole


class IsCustomerOrApiAdmin(BasePermission):
    message = "Customer or administrator role is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {UserRole.CUSTOMER, UserRole.ADMIN}
        )
