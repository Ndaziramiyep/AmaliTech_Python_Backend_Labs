from django.contrib import admin
from .models import ClickEvent


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'owner_id', 'clicked_at', 'referrer']
    search_fields = ['short_code']
    list_filter = ['clicked_at']
