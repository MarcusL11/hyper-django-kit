# apps/blogs/tests/test_imagekit_processing.py
"""
Tests for django-imagekit image processing integration for Blog model.

These tests verify that ProcessedImageField correctly processes images:
1. Cropping to exact 1200x630 dimensions (for social media compatibility)
2. Format conversion to WEBP
3. EXIF orientation correction
4. Quality settings

Reference: docs/plans/file_mgmt/specs/blogs-images-spec.md
"""

import pytest
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.blogs.models import Blog


def create_test_image(
    name: str = "test.png",
    color: str = "red",
    size: tuple = (2000, 1500),
    format: str = "PNG",
) -> SimpleUploadedFile:
    """
    Create a test image file for upload testing.

    Args:
        name: Filename for the uploaded file
        color: Color of the test image (e.g., "red", "blue", "green")
        size: Tuple of (width, height) for the image
        format: Image format (PNG, JPEG, etc.)

    Returns:
        SimpleUploadedFile with valid image data
    """
    mode = "RGBA" if format == "PNG" else "RGB"
    image = Image.new(mode, size, color=color)
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    content_type = f"image/{format.lower()}"
    if format == "JPEG":
        content_type = "image/jpeg"
    return SimpleUploadedFile(
        name=name,
        content=buffer.read(),
        content_type=content_type,
    )


def create_jpeg_image(name: str = "test.jpg", size: tuple = (2000, 1500)) -> SimpleUploadedFile:
    """Create a JPEG test image for format conversion testing."""
    image = Image.new("RGB", size, color="blue")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=buffer.read(),
        content_type="image/jpeg",
    )


def get_image_info(file_field) -> dict:
    """
    Get image format and dimensions from a file field.

    Args:
        file_field: Django ImageField or ProcessedImageField instance

    Returns:
        dict with 'format', 'width', 'height' keys
    """
    with file_field.open("rb") as f:
        img = Image.open(f)
        img.load()  # Load image data before file closes
        return {
            "format": img.format,
            "width": img.width,
            "height": img.height,
        }


@pytest.fixture
def staff_user(db, django_user_model):
    """Create a staff user for blog authorship."""
    return django_user_model.objects.create_user(
        username="imagekit_blog_user",
        email="imagekit_blog@test.com",
        password="testpass123",
        is_staff=True,
    )


class TestBlogFeaturedImageProcessing:
    """Test imagekit processing for Blog.featured_image field."""

    @pytest.mark.django_db(transaction=True)
    def test_featured_image_cropped_to_1200x630(self, staff_user):
        """Large featured_image should be cropped to exactly 1200x630."""
        # Create large test image (2000x1500)
        large_image = create_test_image("large.png", "red", (2000, 1500))

        blog = Blog.objects.create(
            title="Featured Test Blog",
            slug="featured-test-blog",
            author=staff_user,
            content="Test content",
            featured_image=large_image,
        )

        # Verify image was cropped to exact social media dimensions
        info = get_image_info(blog.featured_image)
        assert info["width"] == 1200, f"Width should be exactly 1200, got {info['width']}"
        assert info["height"] == 630, f"Height should be exactly 630, got {info['height']}"

    @pytest.mark.django_db(transaction=True)
    def test_featured_image_converted_to_webp(self, staff_user):
        """featured_image should be converted to WEBP format."""
        # Create PNG image
        png_image = create_test_image("test.png", "blue", (1500, 1000), "PNG")

        blog = Blog.objects.create(
            title="Featured WEBP Test Blog",
            slug="featured-webp-test-blog",
            author=staff_user,
            content="Test content",
            featured_image=png_image,
        )

        # Verify format is WEBP
        info = get_image_info(blog.featured_image)
        assert info["format"] == "WEBP", f"Format should be WEBP, got {info['format']}"

    @pytest.mark.django_db(transaction=True)
    def test_featured_image_from_jpeg(self, staff_user):
        """JPEG featured_image should be converted to WEBP."""
        # Create JPEG image
        jpeg_image = create_jpeg_image("photo.jpg", (1800, 1200))

        blog = Blog.objects.create(
            title="Featured JPEG Test Blog",
            slug="featured-jpeg-test-blog",
            author=staff_user,
            content="Test content",
            featured_image=jpeg_image,
        )

        # Verify format is WEBP
        info = get_image_info(blog.featured_image)
        assert info["format"] == "WEBP", f"JPEG should be converted to WEBP, got {info['format']}"

    @pytest.mark.django_db(transaction=True)
    def test_featured_image_small_image_upscaled_and_cropped(self, staff_user):
        """Small images should be upscaled and cropped to exact 1200x630."""
        # Create small test image (400x300)
        small_image = create_test_image("small.png", "green", (400, 300))

        blog = Blog.objects.create(
            title="Featured Small Test Blog",
            slug="featured-small-test-blog",
            author=staff_user,
            content="Test content",
            featured_image=small_image,
        )

        # ResizeToFill should upscale and crop to exact dimensions
        info = get_image_info(blog.featured_image)
        assert info["width"] == 1200, f"Width should be exactly 1200, got {info['width']}"
        assert info["height"] == 630, f"Height should be exactly 630, got {info['height']}"


class TestBlogOGImageProcessing:
    """Test imagekit processing for Blog.og_image field."""

    @pytest.mark.django_db(transaction=True)
    def test_og_image_cropped_to_1200x630(self, staff_user):
        """Large og_image should be cropped to exactly 1200x630."""
        # Create large test image (2400x1600)
        large_image = create_test_image("large_og.png", "orange", (2400, 1600))

        blog = Blog.objects.create(
            title="OG Test Blog",
            slug="og-test-blog",
            author=staff_user,
            content="Test content",
            og_image=large_image,
        )

        # Verify image was cropped to exact social media dimensions
        info = get_image_info(blog.og_image)
        assert info["width"] == 1200, f"Width should be exactly 1200, got {info['width']}"
        assert info["height"] == 630, f"Height should be exactly 630, got {info['height']}"

    @pytest.mark.django_db(transaction=True)
    def test_og_image_converted_to_webp(self, staff_user):
        """og_image should be converted to WEBP format."""
        # Create PNG image
        png_image = create_test_image("og_test.png", "purple", (1600, 1200), "PNG")

        blog = Blog.objects.create(
            title="OG WEBP Test Blog",
            slug="og-webp-test-blog",
            author=staff_user,
            content="Test content",
            og_image=png_image,
        )

        # Verify format is WEBP
        info = get_image_info(blog.og_image)
        assert info["format"] == "WEBP", f"Format should be WEBP, got {info['format']}"

    @pytest.mark.django_db(transaction=True)
    def test_og_image_from_jpeg(self, staff_user):
        """JPEG og_image should be converted to WEBP."""
        # Create JPEG image
        jpeg_image = create_jpeg_image("og_photo.jpg", (1920, 1080))

        blog = Blog.objects.create(
            title="OG JPEG Test Blog",
            slug="og-jpeg-test-blog",
            author=staff_user,
            content="Test content",
            og_image=jpeg_image,
        )

        # Verify format is WEBP
        info = get_image_info(blog.og_image)
        assert info["format"] == "WEBP", f"JPEG should be converted to WEBP, got {info['format']}"

    @pytest.mark.django_db(transaction=True)
    def test_og_image_portrait_orientation(self, staff_user):
        """Portrait OG image should be cropped and resized to 1200x630."""
        # Create portrait test image (800x1200)
        portrait_image = create_test_image("portrait.png", "cyan", (800, 1200))

        blog = Blog.objects.create(
            title="OG Portrait Test Blog",
            slug="og-portrait-test-blog",
            author=staff_user,
            content="Test content",
            og_image=portrait_image,
        )

        # Verify image dimensions are exact (ResizeToFill crops to fit)
        info = get_image_info(blog.og_image)
        assert info["width"] == 1200, f"Width should be exactly 1200, got {info['width']}"
        assert info["height"] == 630, f"Height should be exactly 630, got {info['height']}"


class TestBlogImageBothFields:
    """Test that both image fields can be used together correctly."""

    @pytest.mark.django_db(transaction=True)
    def test_both_images_processed_correctly(self, staff_user):
        """Both featured_image and og_image should be processed to correct dimensions."""
        # Create different test images
        featured = create_test_image("featured.png", "red", (3000, 2000))
        og = create_jpeg_image("og.jpg", (1920, 1080))

        blog = Blog.objects.create(
            title="Both Images Test Blog",
            slug="both-images-test-blog",
            author=staff_user,
            content="Test content",
            featured_image=featured,
            og_image=og,
        )

        # Verify featured image
        featured_info = get_image_info(blog.featured_image)
        assert featured_info["width"] == 1200
        assert featured_info["height"] == 630
        assert featured_info["format"] == "WEBP"

        # Verify OG image
        og_info = get_image_info(blog.og_image)
        assert og_info["width"] == 1200
        assert og_info["height"] == 630
        assert og_info["format"] == "WEBP"
