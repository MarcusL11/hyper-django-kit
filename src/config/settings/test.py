# config/settings/test.py

from .base import *

# Mark as testing environment
DEBUG = True
TESTING = True

# Use in-memory SQLite for faster tests
# No need to create/destroy database files
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable password hashing for faster user creation in tests
# MD5 is insecure but acceptable for tests since speed matters
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use console email backend (emails won't actually send)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable Stripe in tests
STRIPE_SECRET_KEY = "sk_test_fake_key_for_testing"
STRIPE_LIVE_MODE = False
DJSTRIPE_WEBHOOK_SECRET = "whsec_fake_webhook_secret_for_testing"

# Disable debug toolbar in tests
if "debug_toolbar" in INSTALLED_APPS:
    INSTALLED_APPS.remove("debug_toolbar")

if "debug_toolbar.middleware.DebugToolbarMiddleware" in MIDDLEWARE:
    MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
