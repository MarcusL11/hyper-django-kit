# Blog Content Management System Implementation Plan

## Executive Summary

### Objective
Complete the implementation of an admin-only Blog Content Management system in the Django `blogs` app, featuring Markdown content editing via django-markdownx and SEO metadata support via django-meta.

### Recommended Approach
Implement a robust Blog model with full SEO support using the ModelMeta mixin, integrate MarkdownxModelAdmin for rich content editing in the admin interface, and ensure proper URL configuration for the markdownx AJAX endpoints.

### Key Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing imports in existing models.py | High - Code will not run | Add missing imports for `get_user_model` and `MarkdownxField` |
| Markdownx URLs not configured | High - Image uploads and preview will fail | Add markdownx URLs to root URL configuration |
| django-meta not installed | Medium - SEO features unavailable | Add to requirements and INSTALLED_APPS |
| Missing `__str__` method on Blog model | Low - Poor admin UX | Add `__str__` method |

### Estimated Complexity
**Medium** - The core structure exists but requires completion of imports, model enhancements, admin configuration, and URL setup.

---

## 1. Current State Analysis

### 1.1 Existing Code Review

#### `/Users/mal/Documents/dev/mal/src/apps/blogs/models.py`
```python
from django.db import models
from apps.core.models import BaseModel

# Create your models here.


class Blog(BaseModel):
    title = models.CharField(max_length=200, unique=True)
    url_slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="blogs"
    )
    overview = models.TextField(blank=True, null=True)
    body = MarkdownxField(blank=True, null=True)
    published_date = models.DateField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
```

**Issues Identified:**
1. **Missing import `get_user_model`** - Will cause `NameError` at runtime
2. **Missing import `MarkdownxField`** - Will cause `NameError` at runtime
3. **No `__str__` method** - Required per CLAUDE.md guidelines
4. **No `Meta` class** - Missing verbose names and ordering
5. **Field naming: `url_slug`** - Should be `slug` for consistency with project patterns (see `ShopProduct.slug`)
6. **No SEO metadata support** - django-meta integration missing
7. **No featured image field** - Common blog requirement for SEO and display

#### `/Users/mal/Documents/dev/mal/src/apps/blogs/admin.py`
```python
from django.contrib import admin

# Register your models here.
```
**Status:** Empty - requires full implementation

#### `/Users/mal/Documents/dev/mal/src/apps/blogs/urls.py`
```python
from django.urls import path
from . import views

app_name = "blogs"

urlpatterns = []
```
**Status:** Proper namespace defined, no URLs needed (admin-only)

#### `/Users/mal/Documents/dev/mal/src/apps/blogs/apps.py`
```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blogs"
```
**Issue:** Class name should be `BlogsConfig` (plural) to match app name pattern

#### Root URLs (`/Users/mal/Documents/dev/mal/src/config/urls.py`)
- blogs app URLs are included: `path("blogs/", include("apps.blogs.urls", namespace="blogs"))`
- **Missing:** markdownx URLs for AJAX image upload and preview

#### Settings (`/Users/mal/Documents/dev/mal/src/config/settings/base.py`)
- `apps.blogs` is in `LOCAL_APPS`
- **Missing:** `markdownx` in THIRD_PARTY_APPS (user claims it's configured but not visible in settings)
- **Missing:** `meta` (django-meta) in THIRD_PARTY_APPS
- **Missing:** MARKDOWNX_* settings (user claims configured but not visible)
- **Missing:** META_* settings for django-meta

### 1.2 Naming Convention Validation

| Element | Current | Expected | Status |
|---------|---------|----------|--------|
| App name | `blogs` | `blogs` (plural, snake_case) | PASS |
| Model name | `Blog` | `Blog` (singular, PascalCase) | PASS |
| Field: `url_slug` | `url_slug` | `slug` | FAIL - rename for consistency |
| App config class | `BlogConfig` | `BlogsConfig` | FAIL - should be plural |
| URL namespace | `blogs` | `blogs` | PASS |

---

## 2. Research Findings

### 2.1 django-markdownx Best Practices

**Key Requirements:**
1. Add `markdownx` to `INSTALLED_APPS`
2. Include markdownx URLs in root `urls.py`
3. Configure media path for uploaded images
4. Use `MarkdownxModelAdmin` for admin integration

**Recommended Settings:**
```python
# Already claimed to be configured by user:
MARKDOWNX_MEDIA_PATH = datetime.now().strftime('markdownx/%Y/%m/%d')
MARKDOWNX_UPLOAD_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MARKDOWNX_UPLOAD_MAX_SIZE = 10 * 1024 * 1024  # 10MB
MARKDOWNX_IMAGE_MAX_SIZE = {'size': (1920, 0), 'quality': 85}
MARKDOWNX_SKIP_RESIZE = ['gif']
MARKDOWNX_MARKDOWN_EXTENSIONS = ['markdown.extensions.extra']
```

**URL Configuration Required:**
```python
path('markdownx/', include('markdownx.urls')),
```

### 2.2 django-meta Best Practices

**Key Requirements:**
1. Add `meta` to `INSTALLED_APPS`
2. Use `ModelMeta` mixin on model
3. Define `_metadata` dictionary mapping
4. Configure site-level settings

**Recommended Settings:**
```python
META_SITE_PROTOCOL = 'https'
META_SITE_DOMAIN = 'yourdomain.com'  # Or use META_USE_SITES = True
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True
META_USE_SCHEMAORG_PROPERTIES = True
META_USE_TITLE_TAG = True
```

**Model Integration Pattern:**
```python
from meta.models import ModelMeta

class Blog(ModelMeta, BaseModel):
    _metadata = {
        'title': 'title',
        'description': 'meta_description',
        'image': 'get_meta_image',
        'og_title': 'title',
        'og_description': 'meta_description',
        'twitter_title': 'title',
        'twitter_description': 'meta_description',
    }
```

### 2.3 Project Patterns to Follow

From `/Users/mal/Documents/dev/mal/src/apps/shop/models.py`:
- Use `help_text` for all fields
- Define `Meta` class with `ordering`, `verbose_name`, `verbose_name_plural`
- Include `__str__` method
- Use consistent field naming (`slug` not `url_slug`)
- Add `db_index=True` for frequently queried fields

From `/Users/mal/Documents/dev/mal/src/apps/shop/admin.py`:
- Use `@admin.register()` decorator
- Define `fieldsets` for organized form layout
- Use `readonly_fields` for metadata (id, created_at, updated_at)
- Add `prepopulated_fields` for slug generation

---

## 3. Model Design

### 3.1 Complete Blog Model

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from markdownx.models import MarkdownxField
from markdownx.utils import markdownify
from meta.models import ModelMeta

from apps.core.models import BaseModel


class Blog(ModelMeta, BaseModel):
    """
    Blog post model with Markdown content and SEO metadata support.
    Admin-only content management - no public views required.
    """

    # SEO Metadata mapping for django-meta
    _metadata = {
        "title": "meta_title",
        "description": "meta_description",
        "image": "get_meta_image",
        "og_title": "meta_title",
        "og_description": "meta_description",
        "twitter_title": "meta_title",
        "twitter_description": "meta_description",
        "keywords": "get_meta_keywords",
    }

    # Core Fields
    title = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="Blog post title - displayed as heading and in SEO"
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="URL slug - auto-generated from title if left blank"
    )

    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="blogs",
        help_text="Post author"
    )

    # Content Fields
    overview = models.TextField(
        blank=True,
        help_text="Short summary for blog list pages and SEO description"
    )

    body = MarkdownxField(
        blank=True,
        help_text="Full post content in Markdown format"
    )

    featured_image = models.ImageField(
        upload_to="blogs/featured/%Y/%m/",
        blank=True,
        null=True,
        help_text="Featured image for blog card and SEO og:image"
    )

    featured_image_alt = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for featured image (accessibility)"
    )

    # SEO Fields
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="SEO title (max 70 chars). Uses title if blank."
    )

    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (max 160 chars). Uses overview if blank."
    )

    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords for SEO"
    )

    # Publishing Fields
    published_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Publication date - leave blank for draft"
    )

    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Check to make post publicly visible"
    )

    class Meta:
        ordering = ["-published_date", "-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        indexes = [
            models.Index(fields=["is_published", "published_date"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate model data."""
        from django.core.exceptions import ValidationError

        # Ensure published posts have a publication date
        if self.is_published and not self.published_date:
            raise ValidationError({
                "published_date": "Published posts must have a publication date."
            })

    @property
    def body_html(self):
        """Return the body content as rendered HTML."""
        if self.body:
            return markdownify(self.body)
        return ""

    # SEO Helper Methods for django-meta
    def get_meta_image(self):
        """Return featured image URL for SEO."""
        if self.featured_image:
            return self.featured_image.url
        return None

    def get_meta_keywords(self):
        """Return keywords as list for SEO."""
        if self.meta_keywords:
            return [k.strip() for k in self.meta_keywords.split(",")]
        return []

    @property
    def effective_meta_title(self):
        """Return meta_title or fallback to title."""
        return self.meta_title or self.title

    @property
    def effective_meta_description(self):
        """Return meta_description or fallback to overview."""
        return self.meta_description or self.overview[:160] if self.overview else ""
```

---

## 4. Admin Configuration

### 4.1 Complete Admin Implementation

```python
from django.contrib import admin
from django.db import models
from markdownx.admin import MarkdownxModelAdmin
from markdownx.widgets import AdminMarkdownxWidget

from .models import Blog


@admin.register(Blog)
class BlogAdmin(MarkdownxModelAdmin):
    """
    Admin configuration for Blog posts with Markdown editing support.
    """

    list_display = [
        "title",
        "author",
        "is_published",
        "published_date",
        "created_at",
    ]

    list_filter = [
        "is_published",
        "published_date",
        "author",
        "created_at",
    ]

    search_fields = [
        "title",
        "slug",
        "overview",
        "body",
    ]

    prepopulated_fields = {
        "slug": ("title",),
    }

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
    ]

    autocomplete_fields = [
        "author",
    ]

    date_hierarchy = "published_date"

    fieldsets = [
        (
            "Content",
            {
                "fields": [
                    "title",
                    "slug",
                    "author",
                    "overview",
                    "body",
                ],
            },
        ),
        (
            "Featured Image",
            {
                "fields": [
                    "featured_image",
                    "featured_image_alt",
                ],
            },
        ),
        (
            "SEO Metadata",
            {
                "fields": [
                    "meta_title",
                    "meta_description",
                    "meta_keywords",
                ],
                "classes": ["collapse"],
                "description": "Optional SEO overrides. If blank, defaults to title/overview.",
            },
        ),
        (
            "Publishing",
            {
                "fields": [
                    "is_published",
                    "published_date",
                ],
            },
        ),
        (
            "System Information",
            {
                "fields": [
                    "id",
                    "created_at",
                    "updated_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    # Override TextField widgets to use Markdownx for overview too (optional)
    formfield_overrides = {
        models.TextField: {"widget": AdminMarkdownxWidget},
    }

    def save_model(self, request, obj, form, change):
        """Auto-set author to current user for new posts."""
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
```

---

## 5. URL Configuration

### 5.1 Root URL Configuration Update

Add markdownx URLs to `/Users/mal/Documents/dev/mal/src/config/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("secret-admin-url/", admin.site.urls),
    path("", include("apps.subscriptions.urls", namespace="subscriptions")),
    path("accounts/", include("allauth.urls")),
    path("cookies/", include("cookie_consent.urls")),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("shop/", include("apps.shop.urls", namespace="shop")),
    path("blogs/", include("apps.blogs.urls", namespace="blogs")),
    path(
        "user-dashboard/",
        include("apps.user_dashboard.urls", namespace="user_dashboard"),
    ),
    # Markdownx AJAX endpoints for image upload and preview
    path("markdownx/", include("markdownx.urls")),
]

# ... rest of file unchanged
```

### 5.2 Blogs App URLs (No Changes Needed)

The blogs app `urls.py` is correctly configured with namespace. Since this is admin-only, no public URLs are required.

---

## 6. Settings Configuration

### 6.1 Required Settings Updates

Add to `/Users/mal/Documents/dev/mal/src/config/settings/base.py`:

```python
# In THIRD_PARTY_APPS list, add:
THIRD_PARTY_APPS = [
    # ... existing apps ...
    "markdownx",
    "meta",
]

# After the STORAGES configuration, add:

# ==============================================================================
# MARKDOWNX CONFIGURATION
# ==============================================================================
from datetime import datetime

# Media path with date-based organization
MARKDOWNX_MEDIA_PATH = datetime.now().strftime("markdownx/%Y/%m/%d")

# Allowed upload types
MARKDOWNX_UPLOAD_CONTENT_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]

# Max upload size: 10MB
MARKDOWNX_UPLOAD_MAX_SIZE = 10 * 1024 * 1024

# Auto-resize images (width 1920px, maintain aspect ratio, quality 85)
MARKDOWNX_IMAGE_MAX_SIZE = {"size": (1920, 0), "quality": 85}

# Don't resize GIFs (preserve animation)
MARKDOWNX_SKIP_RESIZE = ["gif"]

# Markdown extensions
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.codehilite",
    "markdown.extensions.toc",
]

# ==============================================================================
# DJANGO-META CONFIGURATION (SEO)
# ==============================================================================

# Protocol for absolute URLs
META_SITE_PROTOCOL = env("META_SITE_PROTOCOL", default="https")

# Site domain (use Sites framework in production or set via env)
META_SITE_DOMAIN = env("META_SITE_DOMAIN", default="localhost:8000")

# Site name for og:site_name
META_SITE_NAME = env("META_SITE_NAME", default="Your Site Name")

# Enable OpenGraph properties
META_USE_OG_PROPERTIES = True

# Enable Twitter Card properties
META_USE_TWITTER_PROPERTIES = True

# Enable Schema.org properties
META_USE_SCHEMAORG_PROPERTIES = True

# Render <title> tags
META_USE_TITLE_TAG = True

# Default OpenGraph type
META_SITE_TYPE = "website"

# Default image if none specified
META_DEFAULT_IMAGE = "/static/images/default-og-image.jpg"

# Twitter site handle (optional)
# META_TWITTER_SITE = "@yourhandle"
```

---

## 7. App Configuration

### 7.1 Update Apps Configuration

Update `/Users/mal/Documents/dev/mal/src/apps/blogs/apps.py`:

```python
from django.apps import AppConfig


class BlogsConfig(AppConfig):
    """Configuration for the blogs app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.blogs"
    verbose_name = "Blog Management"
```

---

## 8. Migration Strategy

### 8.1 Migration Steps

1. **Ensure packages are installed:**
   ```bash
   pip install django-markdownx django-meta Pillow
   ```

2. **Verify settings are updated** (step 6.1)

3. **Create initial migration:**
   ```bash
   source venv/bin/activate
   python manage.py makemigrations blogs
   ```

4. **Review migration file** for correct field definitions

5. **Apply migration:**
   ```bash
   python manage.py migrate blogs
   ```

6. **Collect static files** (required for markdownx):
   ```bash
   python manage.py collectstatic
   ```

---

## 9. Testing Considerations

### 9.1 Model Tests

Create `/Users/mal/Documents/dev/mal/src/apps/blogs/tests.py`:

```python
from datetime import date
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.blogs.models import Blog


User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def blog_post(db, test_user):
    """Create a test blog post."""
    return Blog.objects.create(
        title="Test Blog Post",
        author=test_user,
        overview="This is a test overview.",
        body="# Test Content\n\nThis is **markdown** content.",
        is_published=True,
        published_date=date.today(),
    )


class TestBlogModel:
    """Tests for Blog model."""

    def test_str_method(self, blog_post):
        """Test __str__ returns title."""
        assert str(blog_post) == "Test Blog Post"

    def test_auto_slug_generation(self, db, test_user):
        """Test slug is auto-generated from title."""
        blog = Blog.objects.create(
            title="My Amazing Blog Post",
            author=test_user,
        )
        assert blog.slug == "my-amazing-blog-post"

    def test_body_html_property(self, blog_post):
        """Test body_html renders markdown to HTML."""
        html = blog_post.body_html
        assert "<h1>" in html or "<h1" in html
        assert "<strong>markdown</strong>" in html

    def test_validation_published_requires_date(self, db, test_user):
        """Test that published posts require a publication date."""
        blog = Blog(
            title="Draft Post",
            author=test_user,
            is_published=True,
            published_date=None,
        )
        with pytest.raises(ValidationError) as exc_info:
            blog.full_clean()
        assert "published_date" in exc_info.value.message_dict

    def test_meta_title_fallback(self, blog_post):
        """Test meta_title falls back to title."""
        assert blog_post.effective_meta_title == blog_post.title

        blog_post.meta_title = "Custom SEO Title"
        blog_post.save()
        assert blog_post.effective_meta_title == "Custom SEO Title"

    def test_meta_description_fallback(self, blog_post):
        """Test meta_description falls back to overview."""
        assert blog_post.effective_meta_description == blog_post.overview

    def test_get_meta_keywords(self, blog_post):
        """Test keywords parsing."""
        blog_post.meta_keywords = "python, django, tutorial"
        assert blog_post.get_meta_keywords() == ["python", "django", "tutorial"]

    def test_ordering(self, db, test_user):
        """Test posts are ordered by published_date descending."""
        blog1 = Blog.objects.create(
            title="Post 1",
            author=test_user,
            is_published=True,
            published_date=date(2024, 1, 1),
        )
        blog2 = Blog.objects.create(
            title="Post 2",
            author=test_user,
            is_published=True,
            published_date=date(2024, 6, 1),
        )

        posts = list(Blog.objects.all())
        assert posts[0] == blog2  # More recent first
        assert posts[1] == blog1


class TestBlogAdmin:
    """Tests for Blog admin functionality."""

    @pytest.mark.django_db
    def test_admin_accessible(self, admin_client):
        """Test admin changelist is accessible."""
        response = admin_client.get("/secret-admin-url/blogs/blog/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_admin_add_form(self, admin_client):
        """Test admin add form loads."""
        response = admin_client.get("/secret-admin-url/blogs/blog/add/")
        assert response.status_code == 200
```

### 9.2 Test Commands

```bash
# Run all blog tests
python -m pytest apps/blogs/tests.py -v

# Run with coverage
python -m pytest apps/blogs/tests.py -v --cov=apps.blogs
```

---

## 10. Implementation Checklist

### Phase 1: Dependencies and Settings

- [ ] **1.1** Install required packages
  ```bash
  pip install django-markdownx django-meta Pillow
  ```

- [ ] **1.2** Add `markdownx` to `THIRD_PARTY_APPS` in `base.py`

- [ ] **1.3** Add `meta` to `THIRD_PARTY_APPS` in `base.py`

- [ ] **1.4** Add MARKDOWNX_* settings to `base.py` (Section 6.1)

- [ ] **1.5** Add META_* settings to `base.py` (Section 6.1)

- [ ] **1.6** Add markdownx URLs to root `urls.py` (Section 5.1)

### Phase 2: App Configuration

- [ ] **2.1** Rename `BlogConfig` to `BlogsConfig` in `apps.py`

- [ ] **2.2** Add `verbose_name` to `BlogsConfig`

### Phase 3: Model Implementation

- [ ] **3.1** Update `models.py` with complete Blog model (Section 3.1)
  - Add missing imports
  - Add ModelMeta mixin
  - Add all fields (including SEO fields)
  - Add Meta class
  - Add `__str__` method
  - Add `clean` method for validation
  - Add helper properties and methods

- [ ] **3.2** Create migration
  ```bash
  python manage.py makemigrations blogs
  ```

- [ ] **3.3** Review migration file for correctness

- [ ] **3.4** Apply migration
  ```bash
  python manage.py migrate blogs
  ```

### Phase 4: Admin Implementation

- [ ] **4.1** Update `admin.py` with complete BlogAdmin (Section 4.1)
  - Register Blog with MarkdownxModelAdmin
  - Configure list_display, list_filter, search_fields
  - Configure fieldsets
  - Add prepopulated_fields for slug
  - Add readonly_fields for metadata

### Phase 5: Static Files

- [ ] **5.1** Collect static files for markdownx
  ```bash
  python manage.py collectstatic
  ```

### Phase 6: Testing

- [ ] **6.1** Add tests to `tests.py` (Section 9.1)

- [ ] **6.2** Run tests
  ```bash
  python -m pytest apps/blogs/tests.py -v
  ```

- [ ] **6.3** Fix any failing tests

### Phase 7: Verification

- [ ] **7.1** Start development server
  ```bash
  python manage.py runserver
  ```

- [ ] **7.2** Access admin at `/secret-admin-url/blogs/blog/`

- [ ] **7.3** Create a test blog post with:
  - Title and auto-slug generation
  - Markdown content with live preview
  - Image upload via drag-and-drop
  - Featured image upload
  - SEO metadata fields

- [ ] **7.4** Verify markdown preview works in admin

- [ ] **7.5** Verify image uploads save to correct path

---

## 11. File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `/src/config/settings/base.py` | MODIFY | Add markdownx, meta to apps; add settings |
| `/src/config/urls.py` | MODIFY | Add markdownx URLs |
| `/src/apps/blogs/apps.py` | MODIFY | Rename class to BlogsConfig |
| `/src/apps/blogs/models.py` | REWRITE | Complete model with all fields and methods |
| `/src/apps/blogs/admin.py` | REWRITE | Full admin configuration |
| `/src/apps/blogs/tests.py` | REWRITE | Comprehensive test suite |

---

## 12. Post-Implementation Notes

### Future Enhancements (Out of Scope)

1. **Public Views** - If public blog views are needed later:
   - Add list/detail views
   - Add URL patterns
   - Create templates with django-meta template tags

2. **Categories/Tags** - Could add:
   - BlogCategory model
   - ManyToMany tags field
   - django-taggit integration

3. **Comments** - Could add:
   - Comment model
   - Moderation in admin

4. **Related Posts** - Could add:
   - Algorithm for related content
   - Manual related posts field

### Security Considerations

1. **Image Uploads**: MARKDOWNX_UPLOAD_CONTENT_TYPES restricts to safe image types
2. **File Size**: MARKDOWNX_UPLOAD_MAX_SIZE limits to 10MB
3. **Admin Only**: No public views means reduced attack surface
4. **CSRF**: Django admin has built-in CSRF protection

### Performance Considerations

1. **Database Indexes**: Added on `is_published`, `published_date`, `title`
2. **Composite Index**: Added for common query pattern (published + date)
3. **Image Optimization**: MARKDOWNX_IMAGE_MAX_SIZE auto-resizes uploads

---

## Appendix A: Required Package Versions

```
django-markdownx>=4.0.0
django-meta>=2.4.0
Pillow>=10.0.0
markdown>=3.4.0
```

## Appendix B: Environment Variables

Add to `.env` file:

```
META_SITE_PROTOCOL=https
META_SITE_DOMAIN=yourdomain.com
META_SITE_NAME=Your Site Name
```
