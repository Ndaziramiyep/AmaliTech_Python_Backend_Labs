#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Config.settings")

    if "runserver" in sys.argv:
        # Without an explicit addrport, runserver always falls back to 8000 —
        # which is what every service defaults to, causing collisions when
        # more than one is running locally at once. Default to this service's
        # own PORT (from .env) instead, same port it uses in docker-compose.
        import environ

        env = environ.Env()
        environ.Env.read_env(Path(__file__).resolve().parent / ".env")
        idx = sys.argv.index("runserver") + 1
        if idx >= len(sys.argv) or sys.argv[idx].startswith("-"):
            sys.argv.insert(idx, env("PORT", default="8000"))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
