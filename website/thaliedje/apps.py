from django.apps import AppConfig


class ThaliedjeConfig(AppConfig):
    """The default app config for the Thaliedje app."""

    name = "thaliedje"

    def ready(self):
        """Ready method."""
        from .services import filter_user_page
        from tosti.filter import function_filter

        function_filter.add_filter("tabs_user_page", filter_user_page)
