from django.apps import AppConfig


class PreviewConfig(AppConfig):
    """App config for the preview app — a stateless URL-preview fetcher, no models of its own."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "preview"
