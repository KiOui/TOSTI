from django.apps import AppConfig


class SilvasoftConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "silvasoft"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from silvasoft import signals  # noqa
