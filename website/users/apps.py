from django.apps import AppConfig


class UsersConfig(AppConfig):
    """AppConfig."""

    name = "users"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from users import signals  # noqa
