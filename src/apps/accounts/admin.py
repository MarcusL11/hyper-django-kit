from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "username",
        "is_staff",
        "is_active",
        "created_at",
        "updated_at",
        "customer",
        "subscription",
    ]
    fieldsets = UserAdmin.fieldsets + (
        (None, {"fields": ("subscription", "customer")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {"fields": ("subscription", "customer")}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
