"""Admin registration for the URL model."""

from django.contrib import admin

from .models import URL


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    """Provides a searchable, filterable admin list view for shortened URLs."""

    list_display = ["short_code", "original_url", "owner", "is_active", "click_count", "created_at"]
    search_fields = ["short_code", "custom_alias", "original_url"]
    list_filter = ["is_active", "created_at"]
    readonly_fields = ["short_code", "click_count", "created_at", "updated_at"]
    autocomplete_fields = ["owner"]
