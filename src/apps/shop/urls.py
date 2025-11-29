from django.urls import path
from apps.shop import views

app_name = "shop"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    # Basket Management
    path("basket/", views.view_basket, name="view_basket"),
    path("basket/add/", views.add_to_basket, name="add_to_basket"),
    path(
        "basket/update/<uuid:item_id>/",
        views.update_basket_item,
        name="update_basket_item",
    ),
    path(
        "basket/remove/<uuid:item_id>/",
        views.remove_basket_item,
        name="remove_basket_item",
    ),
    # Checkout Flow
    path(
        "checkout/create-session/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path("order/confirm/", views.order_confirm, name="order_confirm"),
    path("checkout/canceled/", views.checkout_canceled, name="checkout_canceled"),
]
