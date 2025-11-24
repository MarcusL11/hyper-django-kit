# apps/core/admin.py

from django.contrib import admin
from apps.core.models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country', 'created_at']
    list_filter = ['code']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
