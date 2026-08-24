"""Admin registration for the Tag model."""

from django.contrib import admin

from .models import Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Provides a searchable admin list view for tags."""

    list_display = ["name"]
    search_fields = ["name"]
