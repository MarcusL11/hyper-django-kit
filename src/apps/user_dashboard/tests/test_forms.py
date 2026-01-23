import pytest
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from apps.user_dashboard.forms import UserProfileForm
from apps.core.validators import validate_profile_image


@pytest.fixture
def user(db):
    """Create a test user for form instance tests."""
    User = get_user_model()
    return User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")


class TestUserProfileForm:
    """Test suite for UserProfileForm."""

    def test_valid_names(self, user):
        """Form with valid first_name and last_name should be valid."""
        form = UserProfileForm(
            data={"first_name": "John", "last_name": "Doe"},
            instance=user
        )
        assert form.is_valid(), f"Form should be valid, errors: {form.errors}"

    def test_empty_names_valid(self, user):
        """Form with empty first_name and last_name should be valid (both optional)."""
        form = UserProfileForm(
            data={"first_name": "", "last_name": ""},
            instance=user
        )
        assert form.is_valid(), f"Form should be valid with empty names, errors: {form.errors}"

    def test_first_name_with_digits_invalid(self, user):
        """First name with digits should be invalid."""
        form = UserProfileForm(
            data={"first_name": "John123", "last_name": "Doe"},
            instance=user
        )
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_last_name_with_digits_invalid(self, user):
        """Last name with digits should be invalid."""
        form = UserProfileForm(
            data={"first_name": "John", "last_name": "Doe456"},
            instance=user
        )
        assert not form.is_valid()
        assert "last_name" in form.errors

    def test_first_name_too_short(self, user):
        """First name with 1 character should be invalid (min_length=2)."""
        form = UserProfileForm(
            data={"first_name": "J", "last_name": "Doe"},
            instance=user
        )
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_last_name_too_short(self, user):
        """Last name with 1 character should be invalid (min_length=2)."""
        form = UserProfileForm(
            data={"first_name": "John", "last_name": "D"},
            instance=user
        )
        assert not form.is_valid()
        assert "last_name" in form.errors

    def test_names_with_special_chars_valid(self, user):
        """Names with apostrophes and hyphens should be valid."""
        form = UserProfileForm(
            data={"first_name": "O'Brien", "last_name": "Smith-Jones"},
            instance=user
        )
        assert form.is_valid(), f"Form should be valid with special chars, errors: {form.errors}"

    def test_names_with_html_rejected_by_validator(self, user):
        """HTML tags in names are rejected by the RegexValidator (security layer)."""
        form = UserProfileForm(
            data={"first_name": "<script>John</script>", "last_name": "Doe"},
            instance=user
        )
        # RegexValidator rejects < > / chars before clean_first_name runs
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_sanitize_name_strips_html(self):
        """validate_name_field directly strips HTML and validates result."""
        from apps.core.validators import validate_name_field
        # When called directly (bypassing RegexValidator), HTML is stripped
        result = validate_name_field("<b>John</b>", field_name="First name", required=False)
        assert result == "John"

    def test_names_with_unicode_valid(self, user):
        """Names with unicode characters should be valid."""
        form = UserProfileForm(
            data={"first_name": "José", "last_name": "François"},
            instance=user
        )
        assert form.is_valid(), f"Form should be valid with unicode chars, errors: {form.errors}"

    def test_first_name_max_length(self, user):
        """First name exceeding max_length should be invalid."""
        long_name = "J" * 151
        form = UserProfileForm(
            data={"first_name": long_name, "last_name": "Doe"},
            instance=user
        )
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_last_name_max_length(self, user):
        """Last name exceeding max_length should be invalid."""
        long_name = "D" * 151
        form = UserProfileForm(
            data={"first_name": "John", "last_name": long_name},
            instance=user
        )
        assert not form.is_valid()
        assert "last_name" in form.errors

    def test_form_saves_to_user(self, user):
        """Form should save data to user instance correctly."""
        form = UserProfileForm(
            data={"first_name": "John", "last_name": "Doe"},
            instance=user
        )
        assert form.is_valid()
        saved_user = form.save()

        assert saved_user.first_name == "John"
        assert saved_user.last_name == "Doe"

        # Verify user was updated in database
        user.refresh_from_db()
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_meta_fields(self):
        """Form Meta.fields should include all expected fields."""
        expected_fields = ["first_name", "last_name", "profile_image"]
        assert UserProfileForm.Meta.fields == expected_fields


class TestProfileImageValidator:
    """Test suite for profile_image validation."""

    def test_profile_image_too_large(self):
        """Image file exceeding 8MB should be invalid."""
        # Create a mock file larger than 8MB
        large_file = MagicMock()
        large_file.size = 9 * 1024 * 1024  # 9MB
        large_file.content_type = "image/jpeg"
        large_file.name = "large.jpg"

        with pytest.raises(ValidationError) as exc_info:
            validate_profile_image(large_file)

        assert "size" in str(exc_info.value).lower() or "8" in str(exc_info.value)

    def test_profile_image_invalid_type(self):
        """Image file with invalid content type should be invalid."""
        # Create a mock file with invalid type
        invalid_file = MagicMock()
        invalid_file.size = 1 * 1024 * 1024  # 1MB
        invalid_file.content_type = "application/pdf"
        invalid_file.name = "document.pdf"

        with pytest.raises(ValidationError) as exc_info:
            validate_profile_image(invalid_file)

        assert "type" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()

    def test_profile_image_valid_jpeg(self):
        """Valid JPEG image should pass validation."""
        valid_file = MagicMock()
        valid_file.size = 1 * 1024 * 1024  # 1MB
        valid_file.content_type = "image/jpeg"
        valid_file.name = "photo.jpg"

        # Should not raise ValidationError
        try:
            validate_profile_image(valid_file)
        except ValidationError:
            pytest.fail("Valid JPEG should not raise ValidationError")

    def test_profile_image_valid_png(self):
        """Valid PNG image should pass validation."""
        valid_file = MagicMock()
        valid_file.size = 2 * 1024 * 1024  # 2MB
        valid_file.content_type = "image/png"
        valid_file.name = "photo.png"

        # Should not raise ValidationError
        try:
            validate_profile_image(valid_file)
        except ValidationError:
            pytest.fail("Valid PNG should not raise ValidationError")

    def test_profile_image_valid_webp(self):
        """Valid WEBP image should pass validation."""
        valid_file = MagicMock()
        valid_file.size = 1.5 * 1024 * 1024  # 1.5MB
        valid_file.content_type = "image/webp"
        valid_file.name = "photo.webp"

        # Should not raise ValidationError
        try:
            validate_profile_image(valid_file)
        except ValidationError:
            pytest.fail("Valid WEBP should not raise ValidationError")

    def test_profile_image_valid_gif(self):
        """Valid GIF image should pass validation."""
        valid_file = MagicMock()
        valid_file.size = 500 * 1024  # 500KB
        valid_file.content_type = "image/gif"
        valid_file.name = "photo.gif"

        # Should not raise ValidationError
        try:
            validate_profile_image(valid_file)
        except ValidationError:
            pytest.fail("Valid GIF should not raise ValidationError")

    def test_profile_image_exactly_8mb(self):
        """Image file exactly 8MB should be valid."""
        valid_file = MagicMock()
        valid_file.size = 8 * 1024 * 1024  # Exactly 8MB
        valid_file.content_type = "image/jpeg"
        valid_file.name = "photo.jpg"

        # Should not raise ValidationError
        try:
            validate_profile_image(valid_file)
        except ValidationError:
            pytest.fail("8MB image should not raise ValidationError")
