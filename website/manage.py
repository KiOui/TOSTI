#!/usr/bin/env python
"""Django command-line utility for administrative tasks."""
import os
import sys


def main():
    """Django management command."""
    try:
        import tosti.settings.management  # noqa
    except ModuleNotFoundError:
        # Use development settings if no management settings are found
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tosti.settings.development")
    else:
        import socket  # noqa

        hostname = socket.gethostname()
        if hostname.startswith("lilo"):
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tosti.settings.management")
        else:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tosti.settings.production")
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
