"""
URL configuration for subscriptions app.
"""

from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "create-checkout-session/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path(
        "subscription-confirm/", views.subscription_confirm, name="subscription_confirm"
    ),
    # Renamed from checkout_canceled to subscription_canceled
    path(
        "subscription-canceled/",
        views.subscription_canceled,
        name="subscription_canceled",
    ),
    # Keep old URL for backwards compatibility
    path("canceled/", views.subscription_canceled, name="checkout_canceled_legacy"),
    # Billing portal for subscription management
    path("billing-portal/", views.billing_portal, name="billing_portal"),
]
