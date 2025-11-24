# src/apps/conftest.py
"""
Shared pytest fixtures for all apps.

This file imports and re-exports fixtures from individual app conftest.py files,
making them available across all test modules.

Source: pytest documentation - conftest.py files are used to share fixtures
"""

import pytest

# Import fixtures from core app
from apps.core.tests.conftest import (
    language_english,
    language_spanish,
)

# Import fixtures from characters app
from apps.characters.tests.conftest import (
    user,
    character_type_child,
    character_type_adult,
    character_type_dog,
    character_type_cat,
    preset_avatar,
    character_data,
    character,
    character_with_preset_avatar,
    adult_character,
    animal_character,
)

# Import fixtures from book_templates app
from apps.book_templates.tests.conftest import (
    book_series,
    book_template,
    unpublished_book_template,
    character_slot,
    character_slot_2,
    book_template_page,
    book_template_page_with_character_refs,
    book_template_data,
)

# Import fixtures from books app
from apps.books.tests.conftest import (
    book,
    book_character_assignment,
    book_page,
)

# Expose all fixtures by listing them in __all__
__all__ = [
    # Core fixtures
    'language_english',
    'language_spanish',
    # Character fixtures
    'user',
    'character_type_child',
    'character_type_adult',
    'character_type_dog',
    'character_type_cat',
    'preset_avatar',
    'character_data',
    'character',
    'character_with_preset_avatar',
    'adult_character',
    'animal_character',
    # Book template fixtures
    'book_series',
    'book_template',
    'unpublished_book_template',
    'character_slot',
    'character_slot_2',
    'book_template_page',
    'book_template_page_with_character_refs',
    'book_template_data',
    # Book fixtures
    'book',
    'book_character_assignment',
    'book_page',
]
