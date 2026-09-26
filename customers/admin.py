from django.contrib import admin

from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "phone", "user", "created_at")
    search_fields = ("name", "document", "user__email")
    list_select_related = ("user",)
