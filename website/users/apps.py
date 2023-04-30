from django.apps import AppConfig


class UsersConfig(AppConfig):
    """AppConfig."""

    name = "users"

    def ready(self):
        """Register signals."""
        import users.signals  # noqa
        from tosti.management.commands.createfixtures import Command as CreateFixturesCommand
        from users.fixtures import create_fixtures

        def filter_create_fixtures_command(fixture_creators_list: list):
            """Add fixture for orders."""
            fixture_creators_list.append({"app": "users", "creator": create_fixtures})
            return fixture_creators_list

        CreateFixturesCommand.fixture_creators.add_filter(filter_create_fixtures_command)
