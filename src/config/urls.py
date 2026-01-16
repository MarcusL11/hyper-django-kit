from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("secret-admin-url/", admin.site.urls),
    path("", include("apps.landing.urls", namespace="landing")),
    path(
        "subscriptions/", include("apps.subscriptions.urls", namespace="subscriptions")
    ),
    path("accounts/", include("allauth.urls")),
    path("cookies/", include("cookie_consent.urls")),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("shop/", include("apps.shop.urls", namespace="shop")),
    path("blogs/", include("apps.blogs.urls", namespace="blogs")),
    path("markdownx/", include("markdownx.urls")),
    path(
        "user-dashboard/",
        include("apps.user_dashboard.urls", namespace="user_dashboard"),
    ),
]

if settings.DEBUG and not settings.TESTING:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
