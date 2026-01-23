"""
Settings package for Django config.
Automatically loads the correct settings module based on DJANGO_ENVIRONMENT.

Environment Options:
    - development: Local development settings (DEBUG=True, console email)
    - production: Production settings (DEBUG=False, SMTP email, secure cookies)
    - test: Test settings (in-memory DB, faster password hashing)

Usage:
    Set DJANGO_ENVIRONMENT in your .env.base file:
        DJANGO_ENVIRONMENT=development  (default)
        DJANGO_ENVIRONMENT=production
        DJANGO_ENVIRONMENT=test

    Environment files are loaded in order:
        1. .env.base (shared settings, includes DJANGO_ENVIRONMENT)
        2. .env.{environment} (environment-specific overrides)
"""

import os
from pathlib import Path

# Load environment files BEFORE checking environment variable
# Order: .env.base first, then .env.{environment} for overrides
try:
    import environ

    env = environ.Env()
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Load base env file (shared across all environments)
    env_base = os.path.join(BASE_DIR, ".env.base")
    if os.path.exists(env_base):
        environ.Env.read_env(env_file=env_base)

    # Determine environment from .env.base or OS environment
    environment = os.getenv("DJANGO_ENVIRONMENT", "development")

    # Load environment-specific env file (overrides base values)
    env_specific = os.path.join(BASE_DIR, f".env.{environment}")
    if os.path.exists(env_specific):
        environ.Env.read_env(env_file=env_specific, overwrite=True)
except ImportError:
    # django-environ not installed, skip .env loading
    pass

# Determine which environment to use
ENVIRONMENT = os.getenv("DJANGO_ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    from .production import *
elif ENVIRONMENT == "test":
    from .test import *
else:
    # Default to development for safety
    from .development import *
