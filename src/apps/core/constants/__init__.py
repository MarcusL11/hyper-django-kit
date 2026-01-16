"""
Core constants module.

Centralizes shared constants used across the platform.
"""

from .auth import AUTH_LOGIN_URL
from .text_limits import PERSONAL_MESSAGE_LIMIT

__all__ = [
    "AUTH_LOGIN_URL",
    "PERSONAL_MESSAGE_LIMIT",
]
