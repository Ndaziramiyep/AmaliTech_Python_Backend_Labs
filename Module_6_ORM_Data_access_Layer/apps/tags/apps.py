"""App configuration for the tags app."""

from django.apps import AppConfig


class TagsConfig(AppConfig):
    """Registers the tags app, which owns the Tag category model."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tags"
    label = "tags"
