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
        from .services import filter_user_page
        from tosti.filter import function_filter

        function_filter.add_filter("tabs_user_page", filter_user_page)
