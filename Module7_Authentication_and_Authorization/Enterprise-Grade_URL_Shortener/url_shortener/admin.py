from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Click, Tag, Url, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'tier', 'is_premium', 'is_staff']
    list_filter = UserAdmin.list_filter + ('tier', 'is_premium')
    fieldsets = UserAdmin.fieldsets + (
        ('Subscription', {'fields': ('is_premium', 'tier')}),
    )


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    list_display = ['short_code', 'original_url', 'owner', 'is_active', 'click_count', 'created_at']
    search_fields = ['short_code', 'custom_alias', 'original_url', 'owner__email']
    readonly_fields = ['short_code', 'click_count', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    filter_horizontal = ['tags']
    autocomplete_fields = ['owner']


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ['url', 'ip_address', 'country', 'city', 'clicked_at']
    search_fields = ['url__short_code', 'ip_address', 'country', 'city']
    list_filter = ['country', 'clicked_at']
    readonly_fields = ['clicked_at']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
