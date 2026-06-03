from django.apps import AppConfig


class SilvasoftConfig(AppConfig):
    """Silvasoft App Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "silvasoft"

    def ready(self):
        """Register signals."""
        from silvasoft import signals  # noqa
