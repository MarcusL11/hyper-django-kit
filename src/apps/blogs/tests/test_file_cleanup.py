# apps/blogs/tests/test_file_cleanup.py
"""
Tests for django-cleanup file deletion integration for Blog model.

These tests verify that django-cleanup properly deletes files from storage when:
1. Blog instances are deleted
2. Image fields are updated (old file should be deleted)
3. Image fields are cleared

IMPORTANT: These tests use @pytest.mark.django_db(transaction=True) because
django-cleanup uses transaction.on_commit() for file deletion, which only
fires when transactions are committed (not rolled back like in regular TestCase).

Reference: docs/plans/file_mgmt/specs/testing-requirements-spec.md
"""

import pytest
from io import BytesIO

from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.blogs.models import Blog


def create_test_image(name: str = "test.png", color: str = "red", size: tuple = (100, 100)) -> SimpleUploadedFile:
    """
    Create a valid test image file for upload testing.

    Args:
        name: Filename for the uploaded file
        color: Color of the test image (e.g., "red", "blue", "green")
        size: Tuple of (width, height) for the image

    Returns:
        SimpleUploadedFile with valid PNG image data
    """
    image = Image.new("RGB", size, color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=buffer.read(),
        content_type="image/png",
    )


@pytest.fixture
def staff_user(db, django_user_model):
    """Create a staff user for blog authorship."""
    return django_user_model.objects.create_user(
        username="blog_staff_user",
        email="staff@test.com",
        password="testpass123",
        is_staff=True,
    )


class TestBlogFileCleanup:
    """Test django-cleanup integration for Blog model."""

    @pytest.mark.django_db(transaction=True)
    def test_featured_image_deleted_on_model_delete(self, staff_user):
        """Blog featured_image should be deleted from storage when blog is deleted."""
        # Create blog with featured image
        image = create_test_image("featured_test.png", "blue")
        blog = Blog.objects.create(
            title="Test Blog Post",
            slug="test-blog-post",
            author=staff_user,
            content="Test content",
            featured_image=image,
        )

        # Get the storage path before deletion
        image_path = blog.featured_image.name
        assert image_path, "Image path should not be empty"

        # Verify file exists in storage
        assert default_storage.exists(image_path), "Image should exist in storage before deletion"

        # Delete blog
        blog.delete()

        # Verify file is deleted from storage
        assert not default_storage.exists(image_path), "Image should be deleted from storage after model deletion"

    @pytest.mark.django_db(transaction=True)
    def test_og_image_deleted_on_model_delete(self, staff_user):
        """Blog og_image should be deleted from storage when blog is deleted."""
        # Create blog with OG image
        og_img = create_test_image("og_test.png", "green")
        blog = Blog.objects.create(
            title="Test OG Blog",
            slug="test-og-blog",
            author=staff_user,
            content="Test content",
            og_image=og_img,
        )

        # Get the storage path before deletion
        og_path = blog.og_image.name
        assert og_path, "OG image path should not be empty"

        # Verify file exists in storage
        assert default_storage.exists(og_path), "OG image should exist in storage before deletion"

        # Delete blog
        blog.delete()

        # Verify file is deleted from storage
        assert not default_storage.exists(og_path), "OG image should be deleted from storage after model deletion"

    @pytest.mark.django_db(transaction=True)
    def test_both_images_deleted_on_model_delete(self, staff_user):
        """Both featured_image and og_image should be deleted when blog is deleted."""
        # Create blog with both images
        featured_img = create_test_image("featured.png", "red")
        og_img = create_test_image("og.png", "blue")

        blog = Blog.objects.create(
            title="Test Both Images Blog",
            slug="test-both-images-blog",
            author=staff_user,
            content="Test content",
            featured_image=featured_img,
            og_image=og_img,
        )

        featured_path = blog.featured_image.name
        og_path = blog.og_image.name

        # Verify both files exist
        assert default_storage.exists(featured_path), "Featured image should exist before deletion"
        assert default_storage.exists(og_path), "OG image should exist before deletion"

        # Delete blog
        blog.delete()

        # Verify both files are deleted
        assert not default_storage.exists(featured_path), "Featured image should be deleted"
        assert not default_storage.exists(og_path), "OG image should be deleted"

    @pytest.mark.django_db(transaction=True)
    def test_old_featured_image_deleted_on_update(self, staff_user):
        """Old featured_image should be deleted when a new image is assigned."""
        # Create blog with initial image
        old_image = create_test_image("old_featured.png", "red")
        blog = Blog.objects.create(
            title="Test Featured Update Blog",
            slug="test-featured-update-blog",
            author=staff_user,
            content="Test content",
            featured_image=old_image,
        )
        old_path = blog.featured_image.name

        # Verify old image exists
        assert default_storage.exists(old_path), "Old image should exist"

        # Update with new image
        new_image = create_test_image("new_featured.png", "blue")
        blog.featured_image = new_image
        blog.save()

        new_path = blog.featured_image.name

        # Verify old image deleted, new image exists
        assert not default_storage.exists(old_path), "Old image should be deleted after update"
        assert default_storage.exists(new_path), "New image should exist after update"

    @pytest.mark.django_db(transaction=True)
    def test_old_og_image_deleted_on_update(self, staff_user):
        """Old og_image should be deleted when a new OG image is assigned."""
        # Create blog with initial OG image
        old_og = create_test_image("old_og.png", "green")
        blog = Blog.objects.create(
            title="Test OG Update Blog",
            slug="test-og-update-blog",
            author=staff_user,
            content="Test content",
            og_image=old_og,
        )
        old_path = blog.og_image.name

        # Verify old OG image exists
        assert default_storage.exists(old_path), "Old OG image should exist"

        # Update with new OG image
        new_og = create_test_image("new_og.png", "purple")
        blog.og_image = new_og
        blog.save()

        new_path = blog.og_image.name

        # Verify old OG image deleted, new OG image exists
        assert not default_storage.exists(old_path), "Old OG image should be deleted after update"
        assert default_storage.exists(new_path), "New OG image should exist after update"

    @pytest.mark.django_db(transaction=True)
    def test_featured_image_deleted_on_field_clear(self, staff_user):
        """Featured image should be deleted when field is cleared (set to None/empty)."""
        # Create blog with image
        image = create_test_image("to_clear.png", "yellow")
        blog = Blog.objects.create(
            title="Test Clear Featured Blog",
            slug="test-clear-featured-blog",
            author=staff_user,
            content="Test content",
            featured_image=image,
        )
        image_path = blog.featured_image.name

        # Verify image exists
        assert default_storage.exists(image_path), "Image should exist before clearing"

        # Clear the field
        blog.featured_image = None
        blog.save()

        # Verify image is deleted
        assert not default_storage.exists(image_path), "Image should be deleted after field is cleared"

    @pytest.mark.django_db(transaction=True)
    def test_og_image_deleted_on_field_clear(self, staff_user):
        """OG image should be deleted when field is cleared (set to None/empty)."""
        # Create blog with OG image
        og_img = create_test_image("og_to_clear.png", "orange")
        blog = Blog.objects.create(
            title="Test Clear OG Blog",
            slug="test-clear-og-blog",
            author=staff_user,
            content="Test content",
            og_image=og_img,
        )
        og_path = blog.og_image.name

        # Verify OG image exists
        assert default_storage.exists(og_path), "OG image should exist before clearing"

        # Clear the field
        blog.og_image = None
        blog.save()

        # Verify OG image is deleted
        assert not default_storage.exists(og_path), "OG image should be deleted after field is cleared"
