# apps/core/tests/test_models.py

import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.core.models import Language


@pytest.mark.django_db
class TestLanguageModel:
    """
    Test suite for Language model.

    Source: pytest-django documentation - Use @pytest.mark.django_db for database access
    """

    def test_create_language_with_valid_data(self, db):
        """Test creating language with all required fields."""
        language = Language.objects.create(
            name="English",
            code="en",
            country="United States"
        )

        assert language.id is not None
        assert language.name == "English"
        assert language.code == "en"
        assert language.country == "United States"
        assert language.created_at is not None
        assert language.updated_at is not None

    def test_language_str_method(self, language_english):
        """Test __str__ method returns language name."""
        assert str(language_english) == "English"

    def test_language_code_unique_constraint(self, language_english):
        """
        Test unique constraint on code field.

        Source: Django documentation - Test database constraints
        """
        with pytest.raises(IntegrityError):
            Language.objects.create(
                name="British English",
                code="en",  # Duplicate code
                country="United Kingdom"
            )

    def test_language_name_unique_constraint(self, language_english):
        """Test unique constraint on name field."""
        with pytest.raises(IntegrityError):
            Language.objects.create(
                name="English",  # Duplicate name
                code="en-gb",
                country="United Kingdom"
            )

    def test_create_language_with_valid_code_from_settings(self, db):
        """
        Test creating language with valid code from settings.LANGUAGES.

        Source: Django documentation - Use full_clean() to trigger validation
        """
        # English is in settings.LANGUAGES
        language = Language(
            name="English",
            code="en",
            country="United States"
        )
        language.full_clean()  # Should not raise ValidationError
        language.save()

        assert language.code == "en"

    def test_create_language_with_invalid_code(self, db):
        """Test creating language with code not in settings.LANGUAGES raises ValidationError."""
        # 'fr' is not in settings.LANGUAGES (only 'en' and 'es')
        language = Language(
            name="French",
            code="fr",
            country="France"
        )

        with pytest.raises(ValidationError) as exc_info:
            language.full_clean()

        assert "code" in exc_info.value.message_dict

    def test_create_language_without_country(self, db):
        """Test creating language without country (optional field)."""
        language = Language.objects.create(
            name="Spanish",
            code="es"
            # country is optional
        )

        assert language.country is None

    def test_multiple_languages_can_exist(self, language_english, language_spanish):
        """Test multiple language instances can coexist."""
        assert Language.objects.count() == 2
        assert Language.objects.filter(code="en").exists()
        assert Language.objects.filter(code="es").exists()
