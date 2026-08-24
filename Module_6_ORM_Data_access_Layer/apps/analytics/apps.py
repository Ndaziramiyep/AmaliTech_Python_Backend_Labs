"""App configuration for the analytics app."""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """Registers the analytics app, which owns click tracking and reporting."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    label = "analytics"
