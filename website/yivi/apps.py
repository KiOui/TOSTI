from django.apps import AppConfig


class YiviConfig(AppConfig):
    """Yivi App Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "yivi"

    def ready(self):
        """Register signals."""
        from yivi import signals  # noqa
