from django.apps import AppConfig


class AssociationsConfig(AppConfig):
    """Associations app config."""

    name = "associations"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from tosti.management.commands.createfixtures import Command as CreateFixturesCommand
        from associations.fixtures import create_fixtures

        def filter_create_fixtures_command(fixture_creators_list: list):
            """Add fixture for orders."""
            fixture_creators_list.append(create_fixtures)
            return fixture_creators_list

        CreateFixturesCommand.fixture_creators.add_filter(filter_create_fixtures_command)
