from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserverCommand


class Command(StaticfilesRunserverCommand):
    """runserver defaulting to auth-service's own port (8007) instead of Django's 8000."""

    default_port = "8007"
