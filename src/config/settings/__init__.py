"""
Settings package for Django config.
Automatically loads the correct settings module based on DJANGO_ENVIRONMENT.

Environment Options:
    - development: Local development settings (DEBUG=True, console email)
    - production: Production settings (DEBUG=False, SMTP email, secure cookies)
    - test: Test settings (in-memory DB, faster password hashing)

Usage:
    Set DJANGO_ENVIRONMENT in your .env file or as an environment variable:
        DJANGO_ENVIRONMENT=development  (default)
        DJANGO_ENVIRONMENT=production
        DJANGO_ENVIRONMENT=test
"""

import os
from pathlib import Path

# Load .env file BEFORE checking environment variable
# This allows DJANGO_ENVIRONMENT to be set in .env
try:
    import environ

    env = environ.Env()
    # BASE_DIR at this point is the config folder
    BASE_DIR = Path(__file__).resolve().parent.parent
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        environ.Env.read_env(env_file=env_file)
except ImportError:
    # django-environ not installed, skip .env loading
    pass

# Determine which environment to use
# Defaults to 'development' if DJANGO_ENVIRONMENT is not set
ENVIRONMENT = os.getenv("DJANGO_ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    from .production import *
elif ENVIRONMENT == "test":
    from .test import *
else:
    # Default to development for safety
    from .development import *
