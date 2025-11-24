# apps/core/tests/conftest.py

import pytest
from apps.core.models import Language


@pytest.fixture
def language_english(db):
    """
    Create English language instance for testing.

    Source: pytest-django documentation - Use db fixture for database access
    """
    return Language.objects.create(
        name="English",
        code="en",
        country="United States"
    )


@pytest.fixture
def language_spanish(db):
    """
    Create Spanish language instance for testing.

    Source: pytest-django documentation - Use db fixture for database access
    """
    return Language.objects.create(
        name="Spanish",
        code="es",
        country="Spain"
    )
