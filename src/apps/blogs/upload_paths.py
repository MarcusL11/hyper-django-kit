# apps/blogs/upload_paths.py
"""
Upload path functions for blogs app models.

These functions are isolated in their own module to avoid circular imports
between models.py and services.py. They are used by ImageField's upload_to parameter.
"""

from apps.core.utils import sanitize_filename


def blog_featured_image_path(instance, filename):
    """
    Dynamic upload path for blog featured images with filename sanitization.

    Sanitizes the filename to ensure compatibility with S3 and Peecho API.
    Removes Unicode characters (ñ→n, á→a) and invalid filesystem characters.

    Path structure: blogs/{blog.id}/featured/{sanitized_filename}
    Example: blogs/550e8400-e29b-41d4-a716-446655440000/featured/featured_image.jpg

    Args:
        instance: Blog instance
        filename: Original filename from upload (may contain special characters)

    Returns:
        Safe path string with normalized filename (guaranteed non-empty)
    """
    sanitized = sanitize_filename(filename, default_prefix="featured")
    return f"blogs/{instance.id}/featured/{sanitized}"


def blog_og_image_path(instance, filename):
    """
    Dynamic upload path for blog Open Graph images with filename sanitization.

    Sanitizes the filename to ensure compatibility with S3 and Peecho API.
    Removes Unicode characters (ñ→n, á→a) and invalid filesystem characters.

    Path structure: blogs/{blog.id}/og_images/{sanitized_filename}
    Example: blogs/550e8400-e29b-41d4-a716-446655440000/og_images/og_image.png

    Args:
        instance: Blog instance
        filename: Original filename from upload (may contain special characters)

    Returns:
        Safe path string with normalized filename (guaranteed non-empty)
    """
    sanitized = sanitize_filename(filename, default_prefix="og")
    return f"blogs/{instance.id}/og_images/{sanitized}"
