from django.apps import AppConfig


class CustomDjangoCronAppConfig(AppConfig):
    """A custom AppConfig that fixes a bug with default_auto_fields."""

    name = "django_cron"
    default_auto_field = "django.db.models.AutoField"
