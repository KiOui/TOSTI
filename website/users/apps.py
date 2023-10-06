from django.apps import AppConfig


class UsersConfig(AppConfig):
    """AppConfig."""

    name = "users"

    def ready(self):
        """Register signals."""
        from users import signals  # noqa

    def user_account_tabs(self, _):
        """Register user account tabs."""
        from users.views import AccountView

        return [
            {
                "name": "Account",
                "slug": "account",
                "view": AccountView.as_view(),
                "order": 0,
            }
        ]
