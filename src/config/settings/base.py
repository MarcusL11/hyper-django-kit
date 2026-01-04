from pathlib import Path
import sys
import environ
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent  # point to config/ folder
TEMPLATE_DIR = os.path.join(BASE_DIR.parent, "templates")
STATIC_DIR = os.path.join(BASE_DIR.parent, "static")
MEDIA_DIR = os.path.join(BASE_DIR.parent, "media")

env = environ.Env()
environ.Env.read_env(env_file=os.path.join(BASE_DIR, ".env"))


sys.path.insert(0, str(BASE_DIR.parent / "apps"))

TESTING = "test" in sys.argv or "PYTEST_VERSION" in os.environ

SECRET_KEY = env("DJANGO_SECRET_KEY")

# DEBUG is set in environment-specific settings (development.py or production.py)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

DJANGO_CORE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.core",
    "apps.landing",
    "apps.subscriptions",
    "apps.shop",
    "apps.user_dashboard",
    "apps.allauth_ui",
    "apps.theme",  # Tailwind CSS theme app
    "apps.blogs",
]

THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.usersessions",
    "widget_tweaks",
    "slippers",
    "cookie_consent",
    "djstripe",
    "django_cotton.apps.SimpleAppConfig",
    "template_partials.apps.SimpleAppConfig",
    "tailwind",  # Tailwind CSS integration liked to the theme app
]


INSTALLED_APPS = DJANGO_CORE_APPS + LOCAL_APPS + THIRD_PARTY_APPS

TAILWIND_APP_NAME = "apps.theme"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware for django-allauth
    "allauth.account.middleware.AccountMiddleware",
    "allauth.usersessions.middleware.UserSessionsMiddleware",
]

if not TESTING:
    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]


INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

ROOT_URLCONF = "config.urls"

template_dirs = [TEMPLATE_DIR]

for app in LOCAL_APPS:
    app_template_dir = os.path.join(BASE_DIR.parent, app, "templates")
    if os.path.isdir(app_template_dir):
        template_dirs.append(app_template_dir)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": template_dirs,
        "APP_DIRS": False,  # Set to False do to conflicts with Django Cotton and Template Partials
        "OPTIONS": {
            "loaders": [
                (
                    "template_partials.loader.Loader",
                    [
                        (
                            "django.template.loaders.cached.Loader",
                            [
                                "django_cotton.cotton_loader.Loader",
                                "django.template.loaders.filesystem.Loader",
                                "django.template.loaders.app_directories.Loader",
                            ],
                        )
                    ],
                )
            ],
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.user_dashboard.context_processors.user_sidebar_state",
            ],
            "builtins": [
                "django_cotton.templatetags.cotton",
                "template_partials.templatetags.partials",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by email
    "allauth.account.auth_backends.AuthenticationBackend",
]


WSGI_APPLICATION = "config.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Supported languages for book content
LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish (Spain)"),
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [STATIC_DIR, BASE_DIR.parent / "apps" / "theme" / "static"]
STATIC_ROOT = os.path.join(BASE_DIR.parent.parent, "staticfiles_collected")

MEDIA_URL = "/media/"
MEDIA_ROOT = MEDIA_DIR

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.CustomUser"

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

# Default "from" email address
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@email.com")  # type: ignore
SERVER_EMAIL = env("SERVER_EMAIL", default="server@email.com")  # type: ignore

# ========= Django Allauth Settings =========

# Django AllAuth Configuration
# Reference: https://docs.allauth.org/en/latest/account/configuration.html

# Authentication Method: username-based authentication
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"

# Login/Logout Behavior
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/user-dashboard/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_ON_GET = False  # Require POST for logout (security)
ACCOUNT_SESSION_REMEMBER = True  # Remember me functionality
ACCOUNT_SIGNUP_REDIRECT_URL = "/user-dashboard/"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
USERSESSIONS_TRACK_ACTIVITY = True

# Social Account Providers Configuration
# Google OAuth provider - configure in Django admin or via SOCIALACCOUNT_PROVIDERS
# To use Google OAuth:
# 1. Add a SocialApp in Django Admin (Sites > Social Applications)
# 2. Or uncomment and configure SOCIALACCOUNT_PROVIDERS below with your credentials
# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        "APP": {"client_id": "123", "secret": "456", "key": ""}
    }
}

# Social Account Settings
SOCIALACCOUNT_AUTO_SIGNUP = True  # Automatically create account from social login

# ======== DJ-STRIPE Settings =========
# STRIPE_SECRET_KEY and STRIPE_LIVE_MODE are set in environment-specific settings
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

# Wait for Django 6.0 to check and remove if needed DJ Stripe related
FORMS_URLFIELD_ASSUME_HTTPS = True

# Development storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "public": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# ======== Shop App Configuration =========
SHOP_PRODUCTS_PER_PAGE = 8
ORDER_LIST_ITEM_PER_PAGE = 20

DEFAULT_PRODUCT_IMAGE = {
    "url": "https://img.daisyui.com/images/stock/photo-1606107557195-0e29a4b5b4aa.webp"
}
