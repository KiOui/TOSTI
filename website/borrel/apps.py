from django.apps import AppConfig
from django.urls import reverse


class BorrelConfig(AppConfig):
    """Borrel Config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "borrel"

    def ready(self):
        """Ready method."""
        from venues.views import VenueCalendarView
        from borrel import signals  # noqa

        def filter_reservation_button(reservation_buttons: list):
            reservation_buttons.append(
                {
                    "name": "Add borrel reservation",
                    "href": reverse("borrel:add_reservation"),
                }
            )
            return reservation_buttons

        VenueCalendarView.reservation_buttons.add_filter(filter_reservation_button)

    def menu_items(self, request):
        """Render menu items."""
        from borrel.models import BasicBorrelBrevet

        try:
            _ = request.user.basic_borrel_brevet
        except BasicBorrelBrevet.DoesNotExist:
            user_has_borrel_brevet = False
        else:
            user_has_borrel_brevet = True

        if not request.user.is_authenticated or not user_has_borrel_brevet:
            return []

        return [
            {
                "title": "Borrel reservations",
                "url": reverse("borrel:list_reservations"),
                "location": "user",
                "order": 2,
            },
        ]
