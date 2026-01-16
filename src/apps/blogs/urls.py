"""
URL patterns for the blogs app.
"""

from django.urls import path

from . import views

app_name = "blogs"

urlpatterns = [
    # Blog listing (with optional category filter via query param)
    path("", views.blog_list, name="blog_list"),

    # Category-specific listing
    path("category/<slug:slug>/", views.blog_category_list, name="blog_category_list"),

    # Staff-only preview via UUID token
    path("preview/<uuid:preview_token>/", views.blog_preview, name="blog_preview"),

    # Blog detail (must be last to avoid catching other patterns)
    path("<slug:slug>/", views.blog_detail, name="blog_detail"),
]
