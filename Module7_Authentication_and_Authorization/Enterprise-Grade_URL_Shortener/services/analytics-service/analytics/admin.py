from django.contrib import admin
from .models import ClickEvent


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    """Django admin list view for click events."""

    list_display = ['short_code', 'owner_id', 'clicked_at', 'city', 'country', 'referrer']
    search_fields = ['short_code']
    list_filter = ['clicked_at']
