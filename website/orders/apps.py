from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """AppConfig for order app."""

    name = "orders"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from orders import signals  # noqa
