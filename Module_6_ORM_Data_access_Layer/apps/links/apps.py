"""App configuration for the links app."""

from django.apps import AppConfig


class LinksConfig(AppConfig):
    """Registers the links app, which owns the URL model and its shortening logic."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.links"
    label = "links"
