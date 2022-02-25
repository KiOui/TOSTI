from django.apps import AppConfig
from django.urls import reverse


class BorrelConfig(AppConfig):
    """Borrel Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "borrel"

    def ready(self):
        """Ready method."""
        from venues.views import VenueCalendarView

        def filter_reservation_button(reservation_buttons: list):
            reservation_buttons.append(
                {
                    "name": "Add borrel reservation",
                    "href": reverse("borrel:add_reservation"),
                }
            )
            reservation_buttons.append(
                {
                    "name": "View borrel reservations",
                    "href": reverse("borrel:list_reservations"),
                }
            )
            return reservation_buttons

        VenueCalendarView.reservation_buttons.add_filter(filter_reservation_button)
