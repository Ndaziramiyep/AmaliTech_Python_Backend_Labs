"""Admin registration for the User model."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Exposes tier and premium status alongside the default user admin fields."""

    list_display = ["username", "email", "tier", "is_premium", "is_staff"]
    list_filter = ["tier", "is_premium", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Subscription", {"fields": ("tier", "is_premium")}),
    )
