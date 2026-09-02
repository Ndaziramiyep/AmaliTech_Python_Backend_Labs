#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# This service's own port, so `runserver` with no address/port argument
# prints "http://localhost:8004/" instead of Django's 127.0.0.1:8000 default.
DEFAULT_RUNSERVER_ADDR = "localhost:8004"


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    argv = sys.argv
    if len(argv) >= 2 and argv[1] == "runserver" and not any(
        not arg.startswith("-") for arg in argv[2:]
    ):
        argv = argv + [DEFAULT_RUNSERVER_ADDR]

    execute_from_command_line(argv)


if __name__ == "__main__":
    main()
