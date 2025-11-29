from django import forms
from apps.accounts.models import CustomUser
from django.core.validators import MaxLengthValidator
from apps.core.validators import name_validator, validate_name_field, validate_profile_image


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information with comprehensive security validation.

    Security features:
    - RegexValidator for character whitelist (letters, spaces, hyphens, apostrophes)
    - HTML tag stripping to prevent XSS
    - Unicode normalization to prevent homograph attacks
    - Length validation (min/max)
    - Special character sanitization
    - Image file validation (size, type)

    Note: Validation logic is shared via apps.core.validators module
    """

    first_name = forms.CharField(
        max_length=150,
        required=False,
        validators=[name_validator, MaxLengthValidator(150)],
        widget=forms.TextInput(
            attrs={
                "class": "grow",
                "placeholder": "First Name",
            }
        ),
        label="First Name",
        help_text="Your first name (optional, letters only)",
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        validators=[name_validator, MaxLengthValidator(150)],
        widget=forms.TextInput(
            attrs={
                "class": "grow",
                "placeholder": "Last Name",
            }
        ),
        label="Last Name",
        help_text="Your last name (optional, letters only)",
    )

    profile_image = forms.ImageField(
        required=False,
        validators=[validate_profile_image],
        widget=forms.FileInput(
            attrs={
                "class": "file-input file-input-bordered w-full",
                "accept": "image/jpeg,image/png,image/webp,image/gif",
            }
        ),
        label="Profile Picture",
        help_text="Max size 8MB. Formats: JPEG, PNG, WebP, GIF",
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "profile_image"]

    def clean_first_name(self):
        """
        Custom validation for first_name with comprehensive security checks.
        Uses shared validation utilities from apps.core.validators.
        """
        first_name = self.cleaned_data.get("first_name", "")
        return validate_name_field(
            first_name,
            field_name="First name",
            required=False,  # Optional for profile updates
            min_length=2,
            max_length=150
        )

    def clean_last_name(self):
        """
        Custom validation for last_name with comprehensive security checks.
        Uses shared validation utilities from apps.core.validators.
        """
        last_name = self.cleaned_data.get("last_name", "")
        return validate_name_field(
            last_name,
            field_name="Last name",
            required=False,  # Optional for profile updates
            min_length=2,
            max_length=150
        )
