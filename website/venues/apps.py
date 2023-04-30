from django.apps import AppConfig
from django.urls import reverse


class VenuesConfig(AppConfig):
    """App config for venue app."""

    name = "venues"

    def ready(self):
        """Ready method."""
        from venues.views import VenueCalendarView
        from venues import signals  # noqa
        from tosti.management.commands.createfixtures import Command as CreateFixturesCommand
        from venues.fixtures import create_fixtures

        def filter_create_fixtures_command(fixture_creators_list: list):
            """Add fixture for venues."""
            fixture_creators_list.append({"app": "venues", "creator": create_fixtures})
            return fixture_creators_list

        def filter_reservation_button(reservation_buttons: list):
            reservation_buttons.append(
                {
                    "name": "Add venue reservation",
                    "href": reverse("venues:add_reservation"),
                }  # noqa
            )
            return reservation_buttons

        VenueCalendarView.reservation_buttons.add_filter(filter_reservation_button)
        CreateFixturesCommand.fixture_creators.add_filter(filter_create_fixtures_command)
