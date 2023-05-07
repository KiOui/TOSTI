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
        from tosti.management.commands.createfixtures import Command as CreateFixturesCommand
        from borrel.fixtures import create_random_fixtures

        def filter_create_fixtures_command(fixture_creators_list: list):
            """Add fixture for orders."""
            fixture_creators_list.append({"app": "borrel", "creator": create_random_fixtures})
            return fixture_creators_list

        def filter_reservation_button(reservation_buttons: list):
            reservation_buttons.append(
                {
                    "name": "Add borrel reservation",
                    "href": reverse("borrel:add_reservation"),
                }
            )
            return reservation_buttons

        VenueCalendarView.reservation_buttons.add_filter(filter_reservation_button)
        CreateFixturesCommand.fixture_creators.add_filter(filter_create_fixtures_command)
