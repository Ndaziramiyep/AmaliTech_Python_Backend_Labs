from django.contrib import admin
from .models import Tag, Url


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    """Django admin configuration for the Url model."""

    list_display = ['short_url', 'custom_alias', 'original_url', 'owner_email', 'is_active', 'click_count', 'created_at']
    search_fields = ['short_url', 'custom_alias', 'original_url', 'owner_email']
    readonly_fields = ['short_url', 'click_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    filter_horizontal = ['tags']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Django admin configuration for the Tag model."""

    list_display = ['name']
    search_fields = ['name']
