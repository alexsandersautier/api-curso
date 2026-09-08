from rest_framework.permissions import BasePermission

from users.models import UserRole


class IsApiAdmin(BasePermission):
    message = "Administrator role is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )
