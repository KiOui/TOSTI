from django.apps import AppConfig
from django.urls import reverse


class TostiConfig(AppConfig):
    """The default app config for the Tosti app."""

    name = "tosti"

    def ready(self):
        """Register signals and decorate the global MCP server."""
        from tosti import signals  # noqa
        self._configure_mcp_server()

    @staticmethod
    def _configure_mcp_server():
        """Brand the MCP server and stamp per-tool annotations.

        django_mcp_server constructs ``global_mcp_server`` at import time
        with a hard-coded ``"django_mcp_server"`` name, no instructions
        and no icons. We patch the lowlevel ``Server`` instance here in
        ``ready()`` so the Django ORM and settings are guaranteed to be
        available, and so all per-app ``MCPToolset`` subclasses are
        already registered by the time we walk the tool list.

        - ``name`` / ``website_url`` / ``icons`` populate the
          ``serverInfo`` field in the ``initialize`` response, which
          clients render in their connector UI.
        - ``instructions`` is prose loaded into the agent's context so it
          uses the tools correctly. The auto-published
          ``get_server_instructions`` tool also returns this text.
        - Per-tool annotations (readOnlyHint, destructiveHint, …) let
          clients group tools into read/write sections and prompt the
          user before destructive actions.

        Icon URLs are absolute and point at static files directly —
        sidestepping the ``/favicon.ico`` 301 redirect, which some MCP
        clients follow unreliably.
        """
        from django.conf import settings
        from django.templatetags.static import static
        from mcp import types as mcp_types
        from mcp_server import mcp_server as global_mcp_server

        from tosti.mcp import SERVER_INSTRUCTIONS, stamp_tool_annotations

        base = getattr(
            settings, "TOSTI_CANONICAL_URL", "https://tosti.science.ru.nl"
        ).rstrip("/")

        def absolute(path: str) -> str:
            return base + static(path)

        lowlevel = global_mcp_server._mcp_server
        lowlevel.name = "TOSTI"
        lowlevel.website_url = base + "/"
        lowlevel.instructions = SERVER_INSTRUCTIONS
        lowlevel.icons = [
            mcp_types.Icon(
                src=absolute("tosti/favicon/favicon-32x32.png"),
                mimeType="image/png",
                sizes=["32x32"],
            ),
            mcp_types.Icon(
                src=absolute("tosti/favicon/favicon-16x16.png"),
                mimeType="image/png",
                sizes=["16x16"],
            ),
            mcp_types.Icon(
                src=absolute("tosti/favicon/android-chrome-192x192.png"),
                mimeType="image/png",
                sizes=["192x192"],
            ),
            mcp_types.Icon(
                src=absolute("tosti/favicon/android-chrome-512x512.png"),
                mimeType="image/png",
                sizes=["512x512"],
            ),
            mcp_types.Icon(
                src=absolute("tosti/favicon/apple-touch-icon.png"),
                mimeType="image/png",
                sizes=["180x180"],
            ),
        ]

        stamp_tool_annotations()

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
                "slug": "api_credentials",
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
                "slug": "ai-assistant",
                "renderer": explainer_page_mcp_tab,
                "order": 100,
            }
        ]
