from django.apps import AppConfig
from django.urls import reverse


class VenuesConfig(AppConfig):
    """App config for venue app."""

    name = "venues"

    def ready(self):
        """Import signals."""
        from venues import signals  # noqa

    def new_reservation_buttons(self, _):
        """Register new reservation buttons."""
        return [
            {
                "name": "Add venue reservation",
                "href": reverse("venues:add_reservation"),
                "order": 0,
            }
        ]

    def menu_items(self, request):
        """Register menu items."""
        if not request.user.is_authenticated:
            return []

        return [
            {
                "title": "Calendar",
                "url": reverse("venues:calendar"),
                "location": "user",
                "order": 0,
            },
            {
                "title": "Venue reservations",
                "url": reverse("venues:list_reservations"),
                "location": "user",
                "order": 1,
            },
        ]
