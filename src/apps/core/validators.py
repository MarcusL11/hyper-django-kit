"""
Shared validation utilities for the BookIDs application.

This module provides reusable validators and sanitization functions
that can be used across multiple apps (auth, user_dashboard, etc.)
"""

from django.core.validators import RegexValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
import unicodedata
import re


# Validator for allowed characters in names
# Allows: letters (any language), spaces, hyphens, apostrophes, and periods
name_validator = RegexValidator(
    regex=r"^[a-zA-ZÀ-ÿ\s\-'\.]+$",
    message="Name can only contain letters, spaces, hyphens, apostrophes, and periods.",
    code="invalid_name_characters",
)


def sanitize_name(name):
    """
    Sanitize name input using Django built-in functions and Python stdlib.

    Security measures:
    1. Strip HTML tags (prevent XSS)
    2. Normalize Unicode (prevent homograph attacks)
    3. Strip whitespace
    4. Remove control characters
    5. Limit consecutive spaces

    Args:
        name: Raw name input (string)

    Returns:
        Sanitized name string

    Example:
        >>> sanitize_name("  John<script>alert('xss')</script>  Doe  ")
        'John Doe'
    """
    if not name:
        return ""

    # 1. Strip any HTML tags using Django's built-in strip_tags
    name = strip_tags(name)

    # 2. Normalize Unicode to NFKC form (prevents homograph attacks)
    # NFKC: Normalization Form KC (Compatibility Decomposition, followed by Canonical Composition)
    name = unicodedata.normalize("NFKC", name)

    # 3. Strip leading/trailing whitespace
    name = name.strip()

    # 4. Remove any control characters (ASCII 0-31 and 127)
    name = "".join(char for char in name if unicodedata.category(char)[0] != "C")

    # 5. Replace multiple consecutive spaces with single space
    name = re.sub(r"\s+", " ", name)

    return name


def validate_name_field(name, field_name="Name", required=True, min_length=2, max_length=150):
    """
    Comprehensive validation for name fields (first_name, last_name, etc.)

    Validates:
    - Sanitizes input (HTML, Unicode, whitespace)
    - Required check (if applicable)
    - No digits allowed
    - Minimum length validation
    - Maximum length validation
    - Only allowed characters (should be enforced by name_validator)

    Args:
        name: The name string to validate
        field_name: Display name for error messages (default: "Name")
        required: Whether the field is required (default: True)
        min_length: Minimum length requirement (default: 2)
        max_length: Maximum length requirement (default: 150)

    Returns:
        Sanitized and validated name string

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_name_field("John", field_name="First name")
        'John'
        >>> validate_name_field("J", field_name="First name")
        ValidationError: First name must be at least 2 characters long.
    """
    # Sanitize input first
    name = sanitize_name(name)

    # If empty after sanitization
    if not name:
        if required:
            raise ValidationError(
                f"{field_name} is required.",
                code="required",
            )
        else:
            return name

    # Validate no digits
    if any(char.isdigit() for char in name):
        raise ValidationError(
            f"{field_name} cannot contain numbers.",
            code="name_contains_digits",
        )

    # Validate minimum length
    if len(name) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters long.",
            code="name_too_short",
        )

    # Validate maximum length
    if len(name) > max_length:
        raise ValidationError(
            f"{field_name} cannot exceed {max_length} characters.",
            code="name_too_long",
        )

    return name


def validate_profile_image(image):
    """
    Validate uploaded profile image.

    Requirements:
    - Max size: 8MB
    - Allowed formats: JPEG, PNG, WebP, GIF

    Args:
        image: UploadedFile object from Django form

    Returns:
        The validated image object

    Raises:
        ValidationError: If validation fails

    Example:
        >>> validate_profile_image(uploaded_file)
        <UploadedFile: profile.jpg>
    """
    # Check file size (8MB = 8 * 1024 * 1024 bytes)
    max_size = 8 * 1024 * 1024
    if image.size > max_size:
        size_mb = image.size / 1024 / 1024
        raise ValidationError(
            f"File size must be under 8MB. Current size: {size_mb:.1f}MB",
            code="file_too_large",
        )

    # Check file type
    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if hasattr(image, 'content_type') and image.content_type not in allowed_types:
        raise ValidationError(
            "Unsupported file type. Allowed formats: JPEG, PNG, WebP, GIF",
            code="invalid_file_type",
        )

    return image
