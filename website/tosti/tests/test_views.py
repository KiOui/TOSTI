from datetime import timedelta

import freezegun
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application, RefreshToken

from orders.models import OrderVenue, Shift
from venues.models import Venue

User = get_user_model()


class TostiViewTests(TestCase):
    fixtures = ["venues.json"]

    def test_index_view(self):
        with freezegun.freeze_time(timezone.now()):
            venue_pk_1 = Venue.objects.get(pk=1)
            order_venue_1 = OrderVenue.objects.create(venue=venue_pk_1)
            venue_pk_2 = Venue.objects.get(pk=2)
            OrderVenue.objects.create(venue=venue_pk_2)
            Shift.objects.create(
                venue=order_venue_1,
                start=timezone.now(),
                end=timezone.now() + timedelta(hours=4),
            )
            response = self.client.get(reverse("index"))
            self.assertEqual(response.status_code, 200)

    def test_privacy_view(self):
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)

    def test_documentation_view(self):
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)

    def test_oauth_integration_docs_view(self):
        response = self.client.get(reverse("oauth-integration-docs"))
        self.assertEqual(response.status_code, 200)
        # The scope table is rendered from the live oauth2_provider config.
        self.assertContains(response, "orders:order")
        self.assertContains(response, "thaliedje:request")
        # PKCE and dynamic client registration are documented.
        self.assertContains(response, "PKCE")
        self.assertContains(response, "/oauth/register/")

    def test_mcp_tools_docs_view(self):
        response = self.client.get(reverse("mcp-tools-docs"))
        self.assertEqual(response.status_code, 200)
        # Each of the published MCP tools appears, with its toolset group.
        for tool_name in (
            "list_active_shifts",
            "place_order",
            "list_venues",
            "create_venue_reservation",
            "get_player_state",
            "search_tracks",
            "request_song",
        ):
            self.assertContains(response, tool_name)
        for toolset_name in ("OrderTools", "ThaliedjeTools", "VenueTools"):
            self.assertContains(response, toolset_name)
        # Schemas are rendered.
        self.assertContains(response, "Input schema")

    def test_live(self):
        for path in ("/live", "/live/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"ok")

    def test_ready(self):
        for path in ("/ready", "/ready/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"ok")


class ConnectedAppsTabTests(TestCase):
    """Account tab listing apps the user has granted access to."""

    def setUp(self):
        self.user = User.objects.create_user(username="connecteduser", password="x")
        self.client.force_login(self.user)
        # A self-registered MCP client: user=None, public client.
        self.mcp_app = Application.objects.create(
            name="Claude Desktop",
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="https://claude.ai/callback",
            user=None,
            skip_authorization=False,
        )
        # An access + refresh token granting the user access to the MCP app.
        self.access_token = AccessToken.objects.create(
            user=self.user,
            application=self.mcp_app,
            token="access-tok-1",
            scope="read thaliedje:request",
            expires=timezone.now() + timedelta(hours=1),
        )
        self.refresh_token = RefreshToken.objects.create(
            user=self.user,
            application=self.mcp_app,
            token="refresh-tok-1",
            access_token=self.access_token,
        )

    def _account_url(self):
        return reverse("users:account") + "?active=connected_apps"

    def test_lists_the_authorised_application(self):
        response = self.client.get(self._account_url())
        self.assertEqual(response.status_code, 200)
        # The app name shows up in the rendered table row; the revoke form
        # is only rendered per entry, so check for it as a stronger signal.
        self.assertContains(response, "Claude Desktop")
        self.assertContains(response, 'name="action" type="hidden" value="revoke"')
        # Scope codes and descriptions are rendered.
        self.assertContains(response, "thaliedje:request")
        self.assertContains(response, "Request songs on your behalf")

    def test_empty_state_when_no_apps_authorised(self):
        AccessToken.objects.all().delete()
        RefreshToken.objects.all().delete()
        response = self.client.get(self._account_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "authorised any apps yet")

    def test_revoke_action_drops_tokens(self):
        response = self.client.post(
            reverse("users:account"),
            {
                "active": "connected_apps",
                "action": "revoke",
                "application_id": str(self.mcp_app.id),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AccessToken.objects.filter(
                user=self.user, application=self.mcp_app
            ).exists()
        )
        self.assertFalse(
            RefreshToken.objects.filter(
                user=self.user, application=self.mcp_app
            ).exists()
        )
        # Application itself is preserved — it may be shared across users.
        self.assertTrue(Application.objects.filter(id=self.mcp_app.id).exists())

    def test_cannot_revoke_app_user_has_no_token_for(self):
        other_user_app = Application.objects.create(
            name="Someone else's app",
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="https://example.com/cb",
            user=None,
        )
        response = self.client.post(
            reverse("users:account"),
            {
                "active": "connected_apps",
                "action": "revoke",
                "application_id": str(other_user_app.id),
            },
        )
        self.assertEqual(response.status_code, 404)
        # The user's existing tokens for their own app are untouched.
        self.assertTrue(
            AccessToken.objects.filter(
                user=self.user, application=self.mcp_app
            ).exists()
        )

    def test_expired_tokens_do_not_appear(self):
        self.access_token.expires = timezone.now() - timedelta(seconds=1)
        self.access_token.save(update_fields=["expires"])
        response = self.client.get(self._account_url())
        # "Claude Desktop" also appears in the intro paragraph as an example,
        # so check for the revoke form instead — it's only rendered per entry.
        self.assertNotContains(response, 'name="action" type="hidden" value="revoke"')
        self.assertContains(response, "authorised any apps yet")

    def test_unknown_action_returns_404(self):
        response = self.client.post(
            reverse("users:account"),
            {
                "active": "connected_apps",
                "action": "nope",
                "application_id": str(self.mcp_app.id),
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self._account_url())
        # LoginRequiredMixin redirects unauthenticated users.
        self.assertEqual(response.status_code, 302)
