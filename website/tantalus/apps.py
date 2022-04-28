from django.apps import AppConfig


class TantalusConfig(AppConfig):
    """AppConfig for tantalus app."""

    name = "tantalus"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from tantalus import signals  # noqa
