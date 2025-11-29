from django.urls import path
from apps.user_dashboard import views

app_name = "user_dashboard"
urlpatterns = [
    path("", views.index, name="index"),
    path(
        "store-user-sidebar-state/",
        views.store_user_sidebar_state,
        name="store_user_sidebar_state",
    ),
    # Subscription management
    path(
        "subscription/",
        views.subscription_management,
        name="subscription_management",
    ),
    path(
        "subscription/invoices/",
        views.subscription_invoices,
        name="subscription_invoices",
    ),
    path(
        "subscription/plans/",
        views.subscription_plans,
        name="subscription_plans",
    ),
    # Orders management
    path(
        "orders/", views.orders_list, name="orders_list"
    ),  # fix name to singular order
    path("orders/<uuid:order_id>/", views.order_detail, name="order_detail"),
    # Account management
    path("account/profile/", views.account_profile, name="account_profile"),
    path(
        "account/profile/delete-image/",
        views.account_profile_delete_image,
        name="account_profile_delete_image",
    ),
    path("account/email/", views.account_email, name="account_email"),
    path(
        "account/email/remove/", views.account_email_remove, name="account_email_remove"
    ),
    path(
        "account/email/make-primary/",
        views.account_email_make_primary,
        name="account_email_make_primary",
    ),
    path(
        "account/email/resend-verification/",
        views.account_email_resend_verification,
        name="account_email_resend_verification",
    ),
    path(
        "account/password/",
        views.account_password,
        name="account_password",
    ),
    path(
        "account/sessions/",
        views.account_sessions,
        name="account_sessions",
    ),
]
