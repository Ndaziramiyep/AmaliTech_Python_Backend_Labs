from django.apps import AppConfig


class PreviewConfig(AppConfig):
    """App config for the preview app — a stateless URL-preview fetcher, no domain tables of its own."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.preview"
    label = "preview"
