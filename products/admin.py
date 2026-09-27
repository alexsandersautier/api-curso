from django.contrib import admin

from products.models import Product, ProductItem


class ProductItemInline(admin.TabularInline):
    model = ProductItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "category__name")
    list_select_related = ("category",)
    inlines = (ProductItemInline,)


@admin.register(ProductItem)
class ProductItemAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "product", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("sku", "name", "product__name")
    list_select_related = ("product",)
