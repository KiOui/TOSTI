from django.apps import AppConfig
from django.urls import reverse


class VenuesConfig(AppConfig):
    """App config for venue app."""

    name = "venues"

    def ready(self):
        """Ready method."""
        from venues.views import VenueCalendarView
        from venues import signals  # noqa

        def filter_reservation_button(reservation_buttons: list):
            reservation_buttons.append(
                {
                    "name": "Add venue reservation",
                    "href": reverse("venues:add_reservation"),
                }  # noqa
            )
            return reservation_buttons

        VenueCalendarView.reservation_buttons.add_filter(filter_reservation_button)

    def menu_items(self, request):
        """Render menu items."""
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
