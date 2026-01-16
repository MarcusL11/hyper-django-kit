"""
Views for the blogs app.
Handles blog listing, detail, category filtering, and staff preview.
"""

import logging
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import Http404

from apps.core.constants import AUTH_LOGIN_URL
from apps.core.utils import is_staff_user
from .models import Blog, BlogCategory
from .selectors import (
    get_published_blogs,
    get_blog_by_slug,
    get_blog_by_preview_token,
    get_all_categories,
    get_category_by_slug,
    get_related_blogs,
    get_recent_blogs,
    get_featured_blog,
    get_paginated_blogs,
)

logger = logging.getLogger(__name__)

# Pagination configuration
POSTS_PER_PAGE = 12


def blog_list(request):
    """
    Display paginated list of published blog posts.
    Optionally filter by category via ?category=slug query parameter.
    """
    # Get filter parameters
    category_slug = request.GET.get("category")
    active_category = None

    # Get category if filtering (gracefully handle invalid category)
    if category_slug:
        try:
            active_category = get_category_by_slug(slug=category_slug)
        except BlogCategory.DoesNotExist:
            pass  # Invalid category, show all posts

    # Get published blogs, optionally filtered by category
    blogs_queryset = get_published_blogs(category=active_category)

    # Get featured post (first published post on page 1 with no category filter)
    featured_post = None
    page_number = request.GET.get("page", 1)
    if not active_category and str(page_number) == "1":
        featured_post = get_featured_blog(category=active_category)

    # Pagination
    page_obj = get_paginated_blogs(
        blogs_queryset=blogs_queryset,
        page_number=page_number,
        posts_per_page=POSTS_PER_PAGE,
    )

    # Get all active categories for filter navigation
    categories = get_all_categories(active_only=True)

    context = {
        "blogs": page_obj.object_list,
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
        "featured_post": featured_post,
    }

    return render(request, "blogs/blog_list.html", context)


def blog_detail(request, slug):
    """
    Display a single published blog post with related posts.
    """
    try:
        blog = get_blog_by_slug(slug=slug, published_only=True)
    except Blog.DoesNotExist:
        raise Http404("Blog post not found")

    # Get related posts based on shared categories
    related_blogs = get_related_blogs(blog=blog, limit=3)

    # Get recent posts for sidebar
    recent_blogs = get_recent_blogs(limit=5)

    context = {
        "blog": blog,
        "related_blogs": related_blogs,
        "recent_blogs": recent_blogs,
    }

    return render(request, "blogs/blog_detail.html", context)


def blog_category_list(request, slug):
    """
    Display blog posts filtered by category.
    Uses URL path parameter for category (raises 404 if invalid).
    """
    # Verify category exists (strict - raises 404 if not found)
    try:
        category = get_category_by_slug(slug=slug)
    except BlogCategory.DoesNotExist:
        raise Http404("Category not found")

    # Get published blogs filtered by category
    blogs_queryset = get_published_blogs(category=category)

    # Pagination
    page_number = request.GET.get("page", 1)
    page_obj = get_paginated_blogs(
        blogs_queryset=blogs_queryset,
        page_number=page_number,
        posts_per_page=POSTS_PER_PAGE,
    )

    # Get all active categories for filter navigation
    categories = get_all_categories(active_only=True)

    context = {
        "blogs": page_obj.object_list,
        "page_obj": page_obj,
        "categories": categories,
        "active_category": category,
        "featured_post": None,  # No featured post on category pages
    }

    return render(request, "blogs/blog_list.html", context)


@user_passes_test(is_staff_user, login_url=AUTH_LOGIN_URL)
def blog_preview(request, preview_token):
    """
    Staff-only preview of unpublished blog posts via UUID token.
    Allows editors to preview drafts before publishing.

    Security:
    - User must be staff (enforced by decorator)
    - User must be either superuser OR the blog post author
    """
    try:
        blog = get_blog_by_preview_token(preview_token=str(preview_token))
    except Blog.DoesNotExist:
        raise Http404("Preview not found or link has expired")

    # Verify user has permission to preview this blog
    # Allow superusers OR the author of the blog post
    if not (request.user.is_superuser or blog.author == request.user):
        logger.warning(
            "[blogs:blog_preview] User %s attempted to preview blog %s without permission",
            request.user.id,
            blog.id,
            extra={
                "user_id": str(request.user.id),
                "blog_id": str(blog.id),
            },
        )
        raise PermissionDenied("You do not have permission to preview this blog post")

    # Get related posts (even for drafts, show what related posts would appear)
    related_blogs = get_related_blogs(blog=blog, limit=3)

    # Get recent posts for sidebar
    recent_blogs = get_recent_blogs(limit=5)

    context = {
        "blog": blog,
        "related_blogs": related_blogs,
        "recent_blogs": recent_blogs,
        "is_preview": True,  # Flag for template to show preview banner
    }

    return render(request, "blogs/blog_detail.html", context)
