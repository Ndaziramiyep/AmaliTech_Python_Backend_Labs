from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin for the custom User model, exposing the tier and is_premium fields."""

    list_display = DjangoUserAdmin.list_display + ("tier", "is_premium")
    list_filter = DjangoUserAdmin.list_filter + ("tier",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Subscription", {"fields": ("tier", "is_premium")}),
    )
    readonly_fields = ("is_premium",)
