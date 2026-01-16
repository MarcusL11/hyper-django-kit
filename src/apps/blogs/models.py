from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from imagekit.models import ProcessedImageField
from imagekit.processors import Transpose, ResizeToFill
from markdownx.models import MarkdownxField

from apps.core.models import BaseModel
from .upload_paths import blog_featured_image_path, blog_og_image_path

User = get_user_model()

# Reserved slugs that conflict with URL patterns
RESERVED_SLUGS = {"category", "preview"}


class BlogCategory(BaseModel):
    """
    Blog post categories for organizing content.
    Inherits UUID pk, created_at, updated_at from BaseModel.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Category Name"),
        help_text=_("Category name (will be translated)")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version of name (auto-generated)")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Brief description of this category")
    )

    class Meta:
        verbose_name = _("Blog Category")
        verbose_name_plural = _("Blog Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate model fields before saving."""
        super().clean()

        # Check for reserved slugs (case-insensitive)
        if self.slug and self.slug.lower() in RESERVED_SLUGS:
            raise ValidationError({
                "slug": _(
                    "The slug '{slug}' is reserved and cannot be used. "
                    "Reserved slugs: {reserved}"
                ).format(
                    slug=self.slug,
                    reserved=", ".join(sorted(RESERVED_SLUGS))
                )
            })


class Blog(BaseModel):
    """
    Blog post model with multilingual support, SEO fields, and draft preview.

    Inherits from BaseModel:
    - id: UUIDField (primary key)
    - created_at: DateTimeField (indexed)
    - updated_at: DateTimeField (auto-updated)
    """

    # Basic fields
    title = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_("Title"),
        help_text=_("Blog post title (will be translated)")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version of title (auto-generated)")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        limit_choices_to={"is_staff": True},
        verbose_name=_("Author"),
        help_text=_("Only staff members can author blog posts")
    )

    # Content fields (translatable)
    summary = models.TextField(
        blank=True,
        verbose_name=_("Summary"),
        help_text=_("Brief description for list view and SEO (will be translated)")
    )
    content = MarkdownxField(
        verbose_name=_("Content"),
        help_text=_("Main blog post content in Markdown format (will be translated)")
    )

    # Featured image
    featured_image = ProcessedImageField(
        upload_to=blog_featured_image_path,
        max_length=255,
        blank=True,
        null=True,
        processors=[
            Transpose(Transpose.AUTO),  # Fix EXIF orientation
            ResizeToFill(width=1200, height=630),  # Crop to exact 16:9 aspect ratio
        ],
        format="WEBP",
        options={"quality": 80},
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif", "heic", "heif"])
        ],
        verbose_name=_("Featured Image"),
        help_text=_("Main image displayed in blog list (auto-processed to 1200x630 WEBP)"),
    )

    # SEO fields
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("Meta Title"),
        help_text=_("SEO title (60 chars max, defaults to post title if empty)")
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=_("Meta Description"),
        help_text=_("SEO description (160 chars max, defaults to summary if empty)")
    )
    og_image = ProcessedImageField(
        upload_to=blog_og_image_path,
        max_length=255,
        blank=True,
        null=True,
        processors=[
            Transpose(Transpose.AUTO),  # Fix EXIF orientation
            ResizeToFill(width=1200, height=630),  # Crop to exact social media dimensions
        ],
        format="WEBP",
        options={"quality": 80},
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp", "gif", "heic", "heif"])
        ],
        verbose_name=_("Open Graph Image"),
        help_text=_("Image for social media sharing (auto-processed to 1200x630 WEBP)"),
    )
    canonical_url = models.URLField(
        blank=True,
        verbose_name=_("Canonical URL"),
        help_text=_("Canonical URL if this post was originally published elsewhere")
    )

    # Publishing fields
    published = models.BooleanField(
        default=False,
        verbose_name=_("Published"),
        help_text=_("Check to publish this post publicly")
    )
    date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Publication Date"),
        help_text=_("Date to display as publication date")
    )
    preview_token = models.UUIDField(
        blank=True,
        null=True,
        unique=True,
        editable=False,
        verbose_name=_("Preview Token"),
        help_text=_("Secret token for previewing unpublished posts")
    )

    # Relationships
    categories = models.ManyToManyField(
        BlogCategory,
        related_name="blogs",
        blank=True,
        verbose_name=_("Categories"),
        help_text=_("Select categories for this post")
    )

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")
        indexes = [
            models.Index(fields=["-date", "-created_at"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["published", "-date"]),
            models.Index(fields=["author"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """Validate model fields before saving."""
        super().clean()

        # Check for reserved slugs (case-insensitive)
        if self.slug and self.slug.lower() in RESERVED_SLUGS:
            raise ValidationError({
                "slug": _(
                    "The slug '{slug}' is reserved and cannot be used. "
                    "Reserved slugs: {reserved}"
                ).format(
                    slug=self.slug,
                    reserved=", ".join(sorted(RESERVED_SLUGS))
                )
            })

        if self.author_id and not self.author.is_staff:
            raise ValidationError({"author": _("Author must be a staff user.")})

        if self.meta_title and len(self.meta_title) > 60:
            raise ValidationError({
                "meta_title": _("Meta title should be 60 characters or less for optimal SEO.")
            })

        if self.meta_description and len(self.meta_description) > 160:
            raise ValidationError({
                "meta_description": _("Meta description should be 160 characters or less for optimal SEO.")
            })

    def get_meta_title(self):
        """Return meta_title or fall back to title."""
        return self.meta_title or self.title

    def get_meta_description(self):
        """Return meta_description or fall back to summary."""
        return self.meta_description or self.summary

    def get_absolute_url(self):
        """Return the canonical URL for this blog post."""
        from django.urls import reverse
        return reverse("blogs:blog_detail", kwargs={"slug": self.slug})
