from .base import *

DEBUG = True

INSTALLED_APPS += []

MIDDLEWARE += []

# ======== Email Configuration =========
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ======== DJ-STRIPE Settings =========
STRIPE_SECRET_KEY = env("STRIPE_TEST_SECRET_KEY")
STRIPE_LIVE_MODE = False
DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_TEST_WEBHOOK_SECRET")


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# UNCOMMENT BELOW FOR SQLITE CONFIGURATION:
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": os.path.join(BASE_DIR.parent.parent, "local_db", "db.sqlite3"),
#     }
# }

# UNCOMMENT BELOW FOR POSTGRES CONFIGURATION:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": "localhost",
        "PORT": "5432",
    }
}
