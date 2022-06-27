from sp.apps import SPConfig


class CustomSPAppConfig(SPConfig):
    """A custom AppConfig that fixes a bug with default_auto_fields."""

    default_auto_field = "django.db.models.AutoField"
