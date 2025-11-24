from django.contrib import admin
from apps.shop.models import (
    ShopCategory,
    ShopProduct,
    ShopProductImage,
    Basket,
    BasketItem,
    Order,
)


@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "sort_order", "is_active", "product_count"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}

    def product_count(self, obj):
        """Show number of products in category"""
        return obj.products.count()

    product_count.short_description = "Products"


class ShopProductImageInline(admin.TabularInline):
    """Inline for uploading multiple product images"""

    model = ShopProductImage
    extra = 1
    fields = ["image", "alt_text", "sort_order"]
    readonly_fields = []


@admin.register(ShopProduct)
class ShopProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "product_id",
        "slug",
        "category",
        "is_new",
        "is_popular",
        "is_active",
        "sort_order",
    ]
    list_filter = ["category", "is_new", "is_popular", "is_active"]
    search_fields = ["name", "product_id", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ShopProductImageInline]

    fieldsets = [
        (
            "Stripe Product Matching",
            {
                "fields": ["product_id"],
                "description": "Must match a Stripe Product ID from djstripe. "
                'Run "python manage.py djstripe_sync_models Product" first.',
            },
        ),
        (
            "Display Information",
            {"fields": ["name", "slug", "description", "category"]},
        ),
        (
            "Flags & Ordering",
            {"fields": ["is_new", "is_popular", "is_active", "sort_order"]},
        ),
        (
            "Metadata",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ShopProductImage)
class ShopProductImageAdmin(admin.ModelAdmin):
    list_display = ["product", "image", "sort_order", "created_at"]
    list_filter = ["product"]
    search_fields = ["product__name", "alt_text"]


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'line_total_dollars', 'created_at']
    fields = ['product', 'quantity', 'line_total_dollars']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_items', 'total_amount_dollars', 'checked_out', 'created_at']
    list_filter = ['checked_out', 'created_at']
    search_fields = ['id', 'user__email']
    readonly_fields = [
        'id', 'user', 'checked_out', 'created_at', 'updated_at',
        'total_items', 'total_amount_dollars'
    ]
    inlines = [BasketItemInline]

    fieldsets = [
        ('Basket Information', {
            'fields': ['id', 'user', 'checked_out']
        }),
        ('Basket Summary (Read-Only)', {
            'fields': ['total_items', 'total_amount_dollars'],
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def has_add_permission(self, request):
        return False  # Baskets created via user actions only

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent accidental deletion


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'basket', 'product', 'quantity', 'line_total_dollars', 'created_at']
    list_filter = ['created_at', 'basket__checked_out']
    search_fields = ['basket__id', 'product__slug']
    readonly_fields = [
        'id', 'basket', 'product', 'quantity', 'line_total_dollars',
        'created_at', 'updated_at'
    ]

    fieldsets = [
        ('Item Information', {
            'fields': ['id', 'basket', 'product', 'quantity']
        }),
        ('Item Summary (Read-Only)', {
            'fields': ['line_total_dollars'],
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def has_add_permission(self, request):
        return False  # Items created via user actions only

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent accidental deletion


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'amount_dollars', 'currency', 'status',
        'products_count', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['id', 'user__email', 'session__id']
    readonly_fields = [
        'id', 'user', 'session', 'basket',
        'created_at', 'updated_at',
        'amount_dollars', 'currency', 'status', 'products_count'
    ]

    fieldsets = [
        ('Order Information', {
            'fields': ['id', 'user', 'session', 'basket']
        }),
        ('Order Details (Read-Only)', {
            'fields': ['amount_dollars', 'currency', 'status', 'products_count'],
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def has_add_permission(self, request):
        return False  # Orders created via checkout only

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent accidental deletion
