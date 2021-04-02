from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """AppConfig for orders app."""

    name = "orders"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from orders import signals  # noqa
