from django.apps import AppConfig


class AllauthUiConfig(AppConfig):
    name = "apps.allauth_ui"

    def ready(self):
        from django.conf import settings

        settings.ALLAUTH_UI_THEME = getattr(settings, "ALLAUTH_UI_THEME", "light")
