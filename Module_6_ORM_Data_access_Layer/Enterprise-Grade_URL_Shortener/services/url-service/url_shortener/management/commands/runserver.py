from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand


class Command(StaticfilesRunserverCommand):
    """runserver defaulting to url-service's own port (8008) instead of Django's 8000."""

    default_port = "8008"
