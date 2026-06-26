from django.apps import AppConfig
from django.urls import reverse


class TostiConfig(AppConfig):
    """The default app config for the Tosti app."""

    name = "tosti"

    def ready(self):
        """Register signals."""
        from tosti import signals  # noqa

    def menu_items(self, _):
        """Register menu items."""
        return [
            {
                "title": "TOSTI",
                "url": reverse("index"),
                "location": "start",
                "order": 0,
                "extra_classes": ["extra-margin-top-mobile"],
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
        from tosti.views import ConnectedAppsView, OAuthCredentialsRequestView

        return [
            {
                "name": "Connected apps",
                "slug": "connected_apps",
                "view": ConnectedAppsView.as_view(),
                "order": 9,
            },
            {
                "name": "API credentials",
                "slug": "oauth_credentials",
                "view": OAuthCredentialsRequestView.as_view(),
                "order": 10,
            },
        ]

    def explainer_tabs(self, _):
        """Register explainer tabs."""
        from tosti.views import explainer_page_mcp_tab

        return [
            {
                "name": "Connect an AI assistant",
                "slug": "connect-ai-assistant",
                "renderer": explainer_page_mcp_tab,
                "order": 100,
            }
        ]
