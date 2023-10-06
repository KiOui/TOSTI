from django.apps import AppConfig
from django.urls import reverse


class TostiConfig(AppConfig):
    """The default app config for the Tosti app."""

    name = "tosti"

    def menu_items(self, _):
        """Register menu items."""
        return [
            {
                "title": "TOSTI",
                "url": reverse("index"),
                "location": "start",
                "order": 0,
                "extra_classes": "extra-margin-top-mobile",
            },
            {
                "title": "Explainers",
                "url": reverse("explainers"),
                "location": "end",
                "order": 1,
            },
        ]

    def user_account_tabs(self, _):
        """Register user account tabs."""
        from tosti.views import OAuthCredentialsRequestView

        return [
            {
                "name": "OAuth Credentials",
                "slug": "oauth_credentials",
                "view": OAuthCredentialsRequestView.as_view(),
                "order": 10,
            }  # noqa
        ]
