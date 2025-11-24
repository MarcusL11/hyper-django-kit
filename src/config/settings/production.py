from .base import *

DEBUG = False

INSTALLED_APPS += []

MIDDLEWARE += []

# ======== Email Configuration =========
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

# ======== DJ-STRIPE Settings =========
STRIPE_SECRET_KEY = env("STRIPE_LIVE_SECRET_KEY")
STRIPE_LIVE_MODE = True
DJSTRIPE_WEBHOOK_SECRET = env("DJSTRIPE_LIVE_WEBHOOK_SECRET")

# ======== Security Settings =========
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ========= Database Configuration =========
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
