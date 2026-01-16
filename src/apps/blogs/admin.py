from django.contrib import admin
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _, ngettext
from django.urls import reverse
from django.utils.html import format_html
from markdownx.admin import MarkdownxModelAdmin

from .models import Blog, BlogCategory


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    """Admin interface for BlogCategory model."""

    list_display = ("name", "slug", "post_count", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "description")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with annotated published post count."""
        qs = super().get_queryset(request)
        return qs.annotate(
            published_post_count=Count("blogs", filter=Q(blogs__published=True))
        )

    def post_count(self, obj):
        """Display the number of published blog posts in this category."""
        count = obj.published_post_count
        return f"{count} post{'s' if count != 1 else ''}"

    post_count.short_description = "Published Posts"
    post_count.admin_order_field = "published_post_count"


@admin.register(Blog)
class BlogAdmin(MarkdownxModelAdmin):
    """
    Admin interface for Blog model with translation and markdown support.
    Combines MarkdownxModelAdmin (for markdown editing) with TranslationAdmin.
    """

    list_display = (
        "title",
        "author",
        "date",
        "published",
        "preview_link",
        "category_list",
        "created_at",
    )
    list_filter = ("published", "author", "date", "categories")
    search_fields = ("title", "content", "summary", "meta_description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)
    date_hierarchy = "date"
    ordering = ("-date", "-created_at")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "preview_token",
        "preview_url_display",
    )

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("title", "slug", "author", "date", "categories")},
        ),
        (_("Content"), {"fields": ("summary", "content", "featured_image")}),
        (
            _("SEO"),
            {
                "fields": (
                    "meta_title",
                    "meta_description",
                    "og_image",
                    "canonical_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Publishing"),
            {"fields": ("published", "preview_token", "preview_url_display")},
        ),
        (
            _("Metadata"),
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related and prefetch_related."""
        qs = super().get_queryset(request)
        return qs.select_related("author").prefetch_related("categories")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit author choices to staff users only."""
        if db_field.name == "author":
            kwargs["queryset"] = db_field.related_model.objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def preview_link(self, obj):
        """Display a clickable preview link for unpublished posts."""
        if not obj.published and obj.preview_token:
            url = reverse(
                "blogs:blog_preview", kwargs={"preview_token": str(obj.preview_token)}
            )
            return format_html(
                '<a href="{}" target="_blank" class="button">Preview</a>', url
            )
        return "-"

    preview_link.short_description = _("Preview")

    def preview_url_display(self, obj):
        """Display the full preview URL for staff to copy/share."""
        if obj.preview_token:
            path = reverse(
                "blogs:blog_preview", kwargs={"preview_token": str(obj.preview_token)}
            )
            return format_html(
                '<input type="text" value="{}" size="60" readonly '
                'onclick="this.select();" style="font-family: monospace;">',
                path,
            )
        return _("Save post to generate preview URL")

    preview_url_display.short_description = _("Preview URL")

    def category_list(self, obj):
        """Display comma-separated list of categories (max 3)."""
        # Convert to list first to use prefetch cache, then slice
        categories = list(obj.categories.all())[:3]
        if not categories:
            return "-"
        return ", ".join([cat.name for cat in categories])

    category_list.short_description = _("Categories")

    def save_model(self, request, obj, form, change):
        """Save the blog post model."""
        # Note: Preview token generation is handled by the service layer
        # when creating unpublished posts via create_blog_post()
        super().save_model(request, obj, form, change)
