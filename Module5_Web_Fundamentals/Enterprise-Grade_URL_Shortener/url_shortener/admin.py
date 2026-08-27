from django.contrib import admin
from .models import Url


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ['short_url', 'original_url', 'owner', 'created_at']
    search_fields = ['short_url', 'original_url', 'owner__username']
    readonly_fields = ['short_url', 'created_at']
    list_filter = ['created_at']
