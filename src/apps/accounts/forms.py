from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from apps.accounts.models import CustomUser


class CustomUserCreationForm(AdminUserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "subscription", "customer")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "subscription", "customer")
