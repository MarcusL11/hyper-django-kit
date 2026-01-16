"""
Selector layer for blog post queries.
Handles database fetching operations following the service/selector pattern.
"""

import logging
from typing import Optional
from django.db.models import QuerySet, Count, Q

from .models import Blog, BlogCategory

logger = logging.getLogger(__name__)


def get_published_blogs(
    *,
    category: Optional[BlogCategory] = None,
) -> QuerySet[Blog]:
    """
    Get all published blog posts with optimized queries.

    Args:
        category: Optional category to filter by

    Returns:
        QuerySet of published Blog instances ordered by date (newest first)
    """
    queryset = (
        Blog.objects.filter(published=True)
        .select_related("author")
        .prefetch_related("categories")
        .order_by("-date", "-created_at")
    )

    if category:
        queryset = queryset.filter(categories=category)

    return queryset


def get_blog_by_slug(*, slug: str, published_only: bool = True) -> Blog:
    """
    Get a single blog post by slug.

    Args:
        slug: The blog post slug
        published_only: If True, only return published posts

    Returns:
        Blog instance

    Raises:
        Blog.DoesNotExist: If blog not found
    """
    queryset = Blog.objects.select_related("author").prefetch_related("categories")

    if published_only:
        queryset = queryset.filter(published=True)

    return queryset.get(slug=slug)


def get_blog_by_preview_token(*, preview_token: str) -> Blog:
    """
    Get a blog post by its preview token (for unpublished drafts).

    Args:
        preview_token: UUID preview token

    Returns:
        Blog instance (published or unpublished)

    Raises:
        Blog.DoesNotExist: If blog not found with that token
    """
    return (
        Blog.objects.select_related("author")
        .prefetch_related("categories")
        .get(preview_token=preview_token)
    )


def get_all_categories(*, active_only: bool = True) -> QuerySet[BlogCategory]:
    """
    Get all blog categories.

    Args:
        active_only: If True, only return categories with published posts

    Returns:
        QuerySet of BlogCategory instances ordered by name
    """
    queryset = BlogCategory.objects.all()

    if active_only:
        queryset = queryset.annotate(
            post_count=Count("blogs", filter=Q(blogs__published=True))
        ).filter(post_count__gt=0)

    return queryset.order_by("name")


def get_category_by_slug(*, slug: str) -> BlogCategory:
    """
    Get a blog category by slug.

    Args:
        slug: Category slug

    Returns:
        BlogCategory instance

    Raises:
        BlogCategory.DoesNotExist: If category not found
    """
    return BlogCategory.objects.get(slug=slug)


def get_related_blogs(*, blog: Blog, limit: int = 3) -> QuerySet[Blog]:
    """
    Get related blog posts based on shared categories.

    Args:
        blog: The current blog post
        limit: Maximum number of related posts to return

    Returns:
        QuerySet of related Blog instances
    """
    return (
        Blog.objects.filter(
            published=True,
            categories__in=blog.categories.all()
        )
        .exclude(id=blog.id)
        .select_related("author")
        .prefetch_related("categories")
        .distinct()
        .order_by("-date", "-created_at")[:limit]
    )


def get_recent_blogs(*, limit: int = 5) -> QuerySet[Blog]:
    """
    Get most recent published blog posts.

    Args:
        limit: Maximum number of posts to return

    Returns:
        QuerySet of recent Blog instances
    """
    return (
        Blog.objects.filter(published=True)
        .select_related("author")
        .order_by("-date", "-created_at")[:limit]
    )


def get_featured_blog(*, category: Optional[BlogCategory] = None) -> Optional[Blog]:
    """
    Get the featured blog post (most recent published post).

    Args:
        category: Optional category to filter by

    Returns:
        Most recent published Blog instance or None if no posts exist
    """
    blogs_queryset = get_published_blogs(category=category)
    return blogs_queryset.first()


def get_paginated_blogs(
    *,
    blogs_queryset: QuerySet[Blog],
    page_number: int,
    posts_per_page: int = 12,
):
    """
    Paginate a blog queryset and return Django Page object.

    Args:
        blogs_queryset: QuerySet of blogs to paginate
        page_number: Requested page number
        posts_per_page: Number of posts per page (default: 12)

    Returns:
        Django Paginator Page object with:
            - object_list: List of blogs on current page
            - has_previous(): bool
            - has_next(): bool
            - number: Current page number
            - paginator.num_pages: Total number of pages
            - previous_page_number(): Previous page number (if exists)
            - next_page_number(): Next page number (if exists)
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    paginator = Paginator(blogs_queryset, posts_per_page)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return page_obj
