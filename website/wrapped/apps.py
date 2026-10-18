from django.apps import AppConfig


class WrappedConfig(AppConfig):
    """TOSTI Wrapped: a yearly look back at the canteens, shown when configured (see ``wrapped.periods``)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "wrapped"

    def menu_items(self, request):
        """Register menu items."""
        from wrapped.periods import current_period

        if current_period() is None or not request.user.is_authenticated:
            return []
        return [
            {
                "title": "Wrapped",
                # Opens the Wrapped popup on the current page (see wrapped.js).
                "url": "#wrapped",
                "location": "user",
                "order": 10,
            },
        ]

    def page_extras(self, request):
        """Register the Wrapped popup: available on every page while shown, with an invitation to open it once."""
        from wrapped.services import render_popup

        popup = render_popup(request)
        return [popup] if popup else []
