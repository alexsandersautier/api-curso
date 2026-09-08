from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class EmailUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )
    list_display = ("email", "role", "is_active", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("created_at", "updated_at")
