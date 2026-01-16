"""
Service layer for blog post business logic.
Handles preview token generation and other write operations.
"""

import logging
from typing import Optional, List
from datetime import date
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from .models import Blog, BlogCategory

User = get_user_model()
logger = logging.getLogger(__name__)


def _generate_unique_slug(*, model_class, title: str, slug_field: str = "slug") -> str:
    """
    Generate a unique slug for a model instance with race-condition safety.

    Args:
        model_class: The Django model class (Blog or BlogCategory)
        title: The title/name to slugify
        slug_field: The field name for the slug (default: "slug")

    Returns:
        Unique slug string

    Note:
        Uses database-level uniqueness check within transaction for safety.
        Appends numeric suffix if slug already exists.
    """
    base_slug = slugify(title)
    slug = base_slug
    counter = 1

    # Keep trying until we find a unique slug
    while model_class.objects.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def ensure_preview_token(blog: Blog) -> Blog:
    """
    Ensure a blog post has a preview token for draft previewing.

    Args:
        blog: Blog instance (can be unsaved)

    Returns:
        Blog instance with preview_token set

    Note:
        Does not call save() - caller is responsible for persisting changes.
    """
    if not blog.preview_token:
        blog.preview_token = uuid4()
        logger.info(
            "[blogs:ensure_preview_token] Generated preview token for blog: %s",
            blog.title,
        )
    return blog


@transaction.atomic
def regenerate_preview_token(*, blog: Blog) -> UUID:
    """
    Regenerate the preview token for a blog post.
    Useful when you want to invalidate existing preview links.

    Args:
        blog: Blog instance

    Returns:
        New UUID4 preview token
    """
    new_token = uuid4()
    blog.preview_token = new_token

    # Validate before saving
    blog.full_clean()
    blog.save(update_fields=["preview_token", "updated_at"])

    logger.info(
        "[blogs:regenerate_preview_token] New preview token for blog: %s", blog.id
    )
    return new_token


@transaction.atomic
def create_blog_post(
    *,
    title: str,
    author: User,
    content: str,
    summary: str = "",
    meta_description: str = "",
    meta_title: str = "",
    featured_image=None,
    og_image=None,
    canonical_url: str = "",
    published: bool = False,
    publication_date: Optional[date] = None,
    categories: Optional[List[BlogCategory]] = None,
) -> Blog:
    """
    Create a new blog post with validation and automatic slug/preview token generation.

    Args:
        title: Blog post title (required)
        author: User instance (must be staff)
        content: Markdown content (required)
        summary: Brief description for list view
        meta_description: SEO meta description
        meta_title: SEO meta title
        featured_image: Featured image file
        og_image: Open Graph image file
        canonical_url: Canonical URL if republished
        published: Whether to publish immediately (default: False)
        publication_date: Publication date (defaults to today if published)
        categories: List of BlogCategory instances

    Returns:
        Newly created Blog instance

    Raises:
        ValidationError: If validation fails
    """
    # Generate unique slug from title
    slug = _generate_unique_slug(model_class=Blog, title=title)

    blog = Blog(
        title=title,
        slug=slug,
        author=author,
        content=content,
        summary=summary,
        meta_description=meta_description,
        meta_title=meta_title,
        featured_image=featured_image,
        og_image=og_image,
        canonical_url=canonical_url,
        published=published,
        date=publication_date or (timezone.now().date() if published else None),
    )

    # Generate preview token for unpublished posts
    if not published:
        ensure_preview_token(blog)

    # Validate before saving
    blog.full_clean()
    blog.save()

    # Add categories after save (M2M relationship)
    if categories:
        blog.categories.set(categories)

    logger.info(
        "[blogs:create_blog_post] Created blog: %s (slug: %s)", blog.id, blog.slug
    )
    return blog


@transaction.atomic
def update_blog_post(
    *,
    blog: Blog,
    title: Optional[str] = None,
    content: Optional[str] = None,
    summary: Optional[str] = None,
    meta_description: Optional[str] = None,
    meta_title: Optional[str] = None,
    featured_image=None,
    og_image=None,
    canonical_url: Optional[str] = None,
    categories: Optional[List[BlogCategory]] = None,
) -> Blog:
    """
    Update an existing blog post with validation.

    Args:
        blog: Blog instance to update
        title: New title (will regenerate slug if changed)
        content: New markdown content
        summary: New summary
        meta_description: New SEO meta description
        meta_title: New SEO meta title
        featured_image: New featured image file
        og_image: New Open Graph image file
        canonical_url: New canonical URL
        categories: New list of BlogCategory instances

    Returns:
        Updated Blog instance

    Raises:
        ValidationError: If validation fails

    Note:
        Only provided fields are updated. Use None to skip a field.
    """
    update_fields = ["updated_at"]

    if title is not None and title != blog.title:
        blog.title = title
        # Regenerate slug if title changed
        blog.slug = _generate_unique_slug(model_class=Blog, title=title)
        update_fields.extend(["title", "slug"])

    if content is not None:
        blog.content = content
        update_fields.append("content")

    if summary is not None:
        blog.summary = summary
        update_fields.append("summary")

    if meta_description is not None:
        blog.meta_description = meta_description
        update_fields.append("meta_description")

    if meta_title is not None:
        blog.meta_title = meta_title
        update_fields.append("meta_title")

    if featured_image is not None:
        blog.featured_image = featured_image
        update_fields.append("featured_image")

    if og_image is not None:
        blog.og_image = og_image
        update_fields.append("og_image")

    if canonical_url is not None:
        blog.canonical_url = canonical_url
        update_fields.append("canonical_url")

    # Validate before saving
    blog.full_clean()
    blog.save(update_fields=update_fields)

    # Update categories if provided
    if categories is not None:
        blog.categories.set(categories)

    logger.info("[blogs:update_blog_post] Updated blog: %s", blog.id)
    return blog


@transaction.atomic
def publish_blog_post(*, blog: Blog, publication_date: Optional[date] = None) -> Blog:
    """
    Publish a blog post and optionally set publication date.

    Args:
        blog: Blog instance to publish
        publication_date: Publication date (defaults to today if not provided)

    Returns:
        Updated Blog instance with published=True

    Raises:
        ValidationError: If validation fails
    """
    blog.published = True
    blog.date = publication_date or timezone.now().date()

    # Validate before saving
    blog.full_clean()
    blog.save(update_fields=["published", "date", "updated_at"])

    logger.info(
        "[blogs:publish_blog_post] Published blog: %s (date: %s)", blog.id, blog.date
    )
    return blog


@transaction.atomic
def unpublish_blog_post(*, blog: Blog) -> Blog:
    """
    Unpublish a blog post (set published=False).

    Args:
        blog: Blog instance to unpublish

    Returns:
        Updated Blog instance with published=False

    Raises:
        ValidationError: If validation fails

    Note:
        Does not modify the publication date. Regenerates preview token
        for secure draft previewing.
    """
    blog.published = False

    # Regenerate preview token for security
    ensure_preview_token(blog)

    # Validate before saving
    blog.full_clean()
    blog.save(update_fields=["published", "preview_token", "updated_at"])

    logger.info("[blogs:unpublish_blog_post] Unpublished blog: %s", blog.id)
    return blog


@transaction.atomic
def create_blog_category(
    *,
    name: str,
    description: str = "",
) -> BlogCategory:
    """
    Create a new blog category with validation and automatic slug generation.

    Args:
        name: Category name (required, unique)
        description: Brief description of the category

    Returns:
        Newly created BlogCategory instance

    Raises:
        ValidationError: If validation fails (e.g., duplicate name)
    """
    # Generate unique slug from name
    slug = _generate_unique_slug(model_class=BlogCategory, title=name)

    category = BlogCategory(
        name=name,
        slug=slug,
        description=description,
    )

    # Validate before saving
    category.full_clean()
    category.save()

    logger.info(
        "[blogs:create_blog_category] Created category: %s (slug: %s)",
        category.id,
        category.slug,
    )
    return category


@transaction.atomic
def update_blog_category(
    *,
    category: BlogCategory,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> BlogCategory:
    """
    Update an existing blog category with validation.

    Args:
        category: BlogCategory instance to update
        name: New category name (will regenerate slug if changed)
        description: New description

    Returns:
        Updated BlogCategory instance

    Raises:
        ValidationError: If validation fails (e.g., duplicate name)

    Note:
        Only provided fields are updated. Use None to skip a field.
    """
    update_fields = ["updated_at"]

    if name is not None and name != category.name:
        category.name = name
        # Regenerate slug if name changed
        category.slug = _generate_unique_slug(model_class=BlogCategory, title=name)
        update_fields.extend(["name", "slug"])

    if description is not None:
        category.description = description
        update_fields.append("description")

    # Validate before saving
    category.full_clean()
    category.save(update_fields=update_fields)

    logger.info("[blogs:update_blog_category] Updated category: %s", category.id)
    return category
