"""
Transport-level tests for the MCP integration.

App-specific MCP tools are tested in each app's own test module
(``thaliedje/tests/test_mcp.py``, ``orders/tests/test_mcp.py``, ``venues/tests/test_mcp.py``).
This file covers the cross-cutting bits that don't belong to any single app:
the OAuth2 discovery endpoints, dynamic client registration, the ``/mcp``
auth gate (incl. ``WWW-Authenticate`` headers), and the shared
``require_scope`` helper.
"""

import json
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from oauth2_provider.models import Application

from tosti.mcp import require_scope

User = get_user_model()


class _StubRequest:
    """Lightweight stand-in for a Django request inside a tool method."""

    def __init__(self, user, auth=None):
        self.user = user
        self.auth = auth


class OAuthDiscoveryTests(TestCase):
    """RFC 8414 / RFC 9728 discovery endpoints (served by django-oauth-toolkit)."""

    AUTH_SERVER_METADATA_URL = "/.well-known/oauth-authorization-server"
    RESOURCE_METADATA_URL = "/.well-known/oauth-protected-resource"

    def test_authorization_server_metadata_has_required_fields(self):
        response = self.client.get(self.AUTH_SERVER_METADATA_URL)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        for field in (
            "issuer",
            "authorization_endpoint",
            "token_endpoint",
            "registration_endpoint",
            "scopes_supported",
            "response_types_supported",
            "grant_types_supported",
        ):
            self.assertIn(field, data)
        # Public scopes let a user act on their own behalf via a DCR client.
        for scope in ("read", "write", "orders:order", "thaliedje:request"):
            self.assertIn(scope, data["scopes_supported"])

    def test_authorization_server_metadata_hides_restricted_scopes(self):
        """Restricted scopes are reserved for maintainer-issued confidential
        clients (staff shift management, POS transaction creation, music-player
        admin) and must not appear in the public discovery document."""
        response = self.client.get(self.AUTH_SERVER_METADATA_URL)
        data = json.loads(response.content)
        for scope in ("orders:manage", "thaliedje:manage", "transactions:write"):
            self.assertNotIn(scope, data["scopes_supported"])

    def test_authorization_server_metadata_only_advertises_recommended_flow(self):
        """Discovery metadata reflects what we support for *new* integrations.

        Authorization-code + refresh is the public flow. Implicit and password
        are OAuth 2.1-deprecated (and gated off via
        ``COMPLIANT_BCP_RFC9700_{IMPLICIT,PASSWORD}_GRANT``). Client
        credentials is a maintainer-issued exception (confidential client
        provisioned out of band) — not a public capability we want third
        parties to discover.
        """
        response = self.client.get(self.AUTH_SERVER_METADATA_URL)
        data = json.loads(response.content)
        self.assertEqual(
            sorted(data["grant_types_supported"]),
            ["authorization_code", "refresh_token"],
        )
        self.assertEqual(data["response_types_supported"], ["code"])
        # PKCE best practice (COMPLIANT_BCP_RFC9700_PKCE_METHOD): only S256.
        self.assertEqual(data["code_challenge_methods_supported"], ["S256"])
        # RFC 9207 mix-up defense advertised once the AUTHZ_RESPONSE_ISS gate
        # is on.
        self.assertTrue(data["authorization_response_iss_parameter_supported"])

    def test_authorization_server_metadata_issuer_is_root_origin(self):
        """The published issuer must be the origin root, not the /oauth/ mount.

        RFC 9207 uses this exact string as the ``iss`` value in authorization
        responses; a /oauth/-prefixed issuer would fail the mix-up defense.
        """
        response = self.client.get(self.AUTH_SERVER_METADATA_URL)
        data = json.loads(response.content)
        # Depending on OIDC_ISS_ENDPOINT the value is either the canonical URL
        # or the request origin — but never contains ``/oauth`` or ``.well-known``.
        self.assertNotIn("/oauth", data["issuer"])
        self.assertNotIn(".well-known", data["issuer"])

    def test_authorization_server_metadata_advertises_registration_endpoint(self):
        response = self.client.get(self.AUTH_SERVER_METADATA_URL)
        data = json.loads(response.content)
        self.assertTrue(data["registration_endpoint"].endswith("/oauth/register/"))

    def test_protected_resource_metadata_returns_required_fields(self):
        response = self.client.get(self.RESOURCE_METADATA_URL)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("resource", data)
        self.assertIn("authorization_servers", data)
        self.assertIn("scopes_supported", data)
        self.assertEqual(data["bearer_methods_supported"], ["header"])


class WWWAuthenticateHeaderTests(TestCase):
    """Unauthenticated requests to /mcp point at the resource metadata.

    ``TostiOAuth2Authentication`` extends django-oauth-toolkit's RFC 9728
    variant so the ``WWW-Authenticate`` challenge already carries the
    ``resource_metadata`` pointer — no middleware rewrite needed.
    """

    def test_mcp_401_includes_resource_metadata(self):
        response = self.client.post(
            "/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "x"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        header = response.get("WWW-Authenticate", "")
        self.assertIn("Bearer", header)
        self.assertIn('resource_metadata="', header)
        self.assertIn(".well-known/oauth-protected-resource", header)


class AuthorizeConsentScreenTests(TestCase):
    """Custom TOSTI-branded consent screen with the right CSP loosening."""

    def setUp(self):
        self.user = User.objects.create_user(username="consenter", password="x")
        self.client.force_login(self.user)
        self.application = Application.objects.create(
            name="Test MCP client",
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="https://claude.ai/api/mcp/auth_callback",
            user=None,
            skip_authorization=False,
        )

    def _authorize_url(self):
        return (
            "/oauth/authorize/"
            f"?client_id={self.application.client_id}"
            "&response_type=code"
            "&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            "&scope=read"
            "&state=xyz"
            "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
            "&code_challenge_method=S256"
        )

    def test_consent_screen_renders_with_tosti_base(self):
        response = self.client.get(self._authorize_url())
        self.assertEqual(response.status_code, 200)
        # Uses TOSTI's base.html (the override), not the upstream package
        # template that pulls in bootstrapcdn.
        self.assertContains(response, "Authorise")
        self.assertContains(response, "Test MCP client")
        self.assertNotContains(response, "netdna.bootstrapcdn.com")

    def test_consent_screen_loosens_form_action_csp(self):
        response = self.client.get(self._authorize_url())
        # The csp_update decorator stamps the response so the CSP middleware
        # merges in the override.
        self.assertEqual(response._csp_update, {"form-action": ["https:"]})

    def _multi_scope_url(self):
        """Authorize URL requesting three scopes."""
        return (
            "/oauth/authorize/"
            f"?client_id={self.application.client_id}"
            "&response_type=code"
            "&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            "&scope=read+orders%3Aorder+thaliedje%3Arequest"
            "&state=xyz"
            "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
            "&code_challenge_method=S256"
        )

    def test_consent_renders_one_checkbox_per_requested_scope(self):
        response = self.client.get(self._multi_scope_url())
        self.assertEqual(response.status_code, 200)
        # One checkbox per requested scope, all checked by default.
        for scope in ("read", "orders:order", "thaliedje:request"):
            self.assertContains(response, f'value="{scope}"')
            self.assertContains(response, f"<code>{scope}</code>")
        # Scopes the client did NOT ask for must not appear as choices.
        self.assertNotContains(response, 'value="thaliedje:manage"')

    def test_granting_subset_issues_code_for_subset(self):
        """User unchecks one scope → the issued grant matches the subset."""
        from oauth2_provider.models import Grant

        get_response = self.client.get(self._multi_scope_url())
        form_initial = get_response.context["form"].initial
        post_response = self.client.post(
            "/oauth/authorize/",
            {
                "csrfmiddlewaretoken": "ignored-in-tests",
                "client_id": form_initial["client_id"],
                "state": form_initial["state"],
                "redirect_uri": form_initial["redirect_uri"],
                "response_type": form_initial["response_type"],
                "code_challenge": form_initial["code_challenge"],
                "code_challenge_method": form_initial["code_challenge_method"],
                "requested_scope": "read orders:order thaliedje:request",
                # User ticks only "read" — drops orders:order and thaliedje:request.
                "scope": ["read"],
                "allow": "Authorize",
            },
        )
        self.assertEqual(post_response.status_code, 302)
        grant = Grant.objects.get(user=self.user, application=self.application)
        self.assertEqual(set(grant.scope.split()), {"read"})

    def test_cannot_grant_scopes_not_originally_requested(self):
        """Tampered POST with a scope the client never asked for is rejected."""
        get_response = self.client.get(self._multi_scope_url())
        form_initial = get_response.context["form"].initial
        post_response = self.client.post(
            "/oauth/authorize/",
            {
                "client_id": form_initial["client_id"],
                "state": form_initial["state"],
                "redirect_uri": form_initial["redirect_uri"],
                "response_type": form_initial["response_type"],
                "code_challenge": form_initial["code_challenge"],
                "code_challenge_method": form_initial["code_challenge_method"],
                "requested_scope": "read",
                "scope": ["read", "thaliedje:manage"],  # not in choices
                "allow": "Authorize",
            },
        )
        # Re-renders the form with an invalid-choice error rather than
        # issuing a grant for the unrequested scope.
        self.assertEqual(post_response.status_code, 200)

    def test_dcr_application_cannot_request_restricted_scope(self):
        """A DCR-registered client cannot request maintainer-only scopes.

        The scopes backend (``TostiScopes``) filters ``RESTRICTED_SCOPES`` out
        of ``get_available_scopes`` for any application with
        ``registration_source="dcr"``. Requesting one should trip the library's
        ``validate_scopes`` and produce an ``invalid_scope`` error response.
        """
        dcr_app = Application.objects.create(
            name="Rogue MCP client",
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="https://claude.ai/api/mcp/auth_callback",
            registration_source=Application.RegistrationSource.DCR,
            user=None,
            skip_authorization=False,
        )
        response = self.client.get(
            "/oauth/authorize/"
            f"?client_id={dcr_app.client_id}"
            "&response_type=code"
            "&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            "&scope=read+orders%3Amanage"
            "&state=xyz"
            "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
            "&code_challenge_method=S256"
        )
        # oauthlib bounces invalid-scope requests back to the client via the
        # redirect_uri (query string) rather than rendering the consent screen.
        self.assertEqual(response.status_code, 302)
        self.assertIn("error=invalid_scope", response["Location"])

    def test_manually_provisioned_application_may_request_restricted_scope(self):
        """A confidential app provisioned by a maintainer keeps full access."""
        # self.application above defaults to registration_source="manual".
        response = self.client.get(
            "/oauth/authorize/"
            f"?client_id={self.application.client_id}"
            "&response_type=code"
            "&redirect_uri=https://claude.ai/api/mcp/auth_callback"
            "&scope=read+orders%3Amanage"
            "&state=xyz"
            "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
            "&code_challenge_method=S256"
        )
        # Consent screen renders — the scope is legal for this application.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "orders:manage")

    def test_granting_zero_scopes_re_renders_with_required_error(self):
        """Submitting with all boxes unticked must not produce a grant."""
        get_response = self.client.get(self._multi_scope_url())
        form_initial = get_response.context["form"].initial
        post_response = self.client.post(
            "/oauth/authorize/",
            {
                "client_id": form_initial["client_id"],
                "state": form_initial["state"],
                "redirect_uri": form_initial["redirect_uri"],
                "response_type": form_initial["response_type"],
                "code_challenge": form_initial["code_challenge"],
                "code_challenge_method": form_initial["code_challenge_method"],
                "requested_scope": "read orders:order",
                "scope": [],
                "allow": "Authorize",
            },
        )
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Select at least one permission")


class DynamicClientRegistrationTests(TestCase):
    """RFC 7591 dynamic client registration.

    The endpoint itself is django-oauth-toolkit's. TOSTI configures it via
    ``RateLimitedAnonymousDCRPermission`` (anonymous access + per-IP cap) and
    wraps it with ``DCRLandingView`` to serve an HTML explainer to browsers.
    """

    DCR_URL = "/oauth/register/"

    def setUp(self):
        cache.clear()

    def _post(self, payload, token_endpoint_auth_method="none"):
        # Every real MCP client registers as a public + PKCE + none client;
        # bake that default in so each test focuses on its own variation.
        body = {"token_endpoint_auth_method": token_endpoint_auth_method}
        body.update(payload)
        return self.client.post(
            self.DCR_URL,
            data=json.dumps(body),
            content_type="application/json",
        )

    def test_minimum_valid_payload_creates_application(self):
        response = self._post({"redirect_uris": ["https://example.com/callback"]})
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        self.assertIn("client_id", body)
        self.assertEqual(body["token_endpoint_auth_method"], "none")
        self.assertEqual(body["redirect_uris"], ["https://example.com/callback"])
        # RFC 7592 management: the response includes a registration access token
        # + a client-configuration URI. The client uses these to later
        # update/delete its own registration.
        self.assertIn("registration_access_token", body)
        self.assertTrue(body["registration_access_token"])
        self.assertIn("registration_client_uri", body)
        self.assertIn(
            f"/oauth/register/{body['client_id']}/", body["registration_client_uri"]
        )
        # The application is persisted as a public auth-code client sourced
        # from DCR.
        app = Application.objects.get(client_id=body["client_id"])
        self.assertEqual(app.client_type, Application.CLIENT_PUBLIC)
        self.assertEqual(
            app.authorization_grant_type, Application.GRANT_AUTHORIZATION_CODE
        )
        self.assertEqual(app.registration_source, Application.RegistrationSource.DCR)

    def test_disallowed_redirect_scheme_is_rejected(self):
        response = self._post({"redirect_uris": ["javascript:alert(1)"]})
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        # The library reports failures from Application.full_clean() (which
        # enforces ALLOWED_REDIRECT_URI_SCHEMES) as invalid_client_metadata.
        self.assertEqual(body["error"], "invalid_client_metadata")

    def test_missing_redirect_uris_is_rejected(self):
        response = self._post({})
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_client_metadata")

    def test_client_name_is_stored(self):
        response = self._post(
            {
                "redirect_uris": ["https://example.com/cb"],
                "client_name": "Claude Desktop test",
            }
        )
        body = json.loads(response.content)
        app = Application.objects.get(client_id=body["client_id"])
        self.assertEqual(app.name, "Claude Desktop test")

    def test_browser_get_returns_html_landing(self):
        response = self.client.get(
            self.DCR_URL,
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dynamic client registration", response.content)
        self.assertEqual(response["Content-Type"].split(";")[0], "text/html")

    def test_non_browser_get_returns_405(self):
        response = self.client.get(
            self.DCR_URL,
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_is_rejected(self):
        response = self.client.post(
            self.DCR_URL,
            data="this is not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_rate_limit_kicks_in(self):
        for _ in range(10):
            response = self._post({"redirect_uris": ["https://example.com/cb"]})
            self.assertEqual(response.status_code, 201)
        response = self._post({"redirect_uris": ["https://example.com/cb"]})
        # RateLimitedAnonymousDCRPermission returns False past the cap, and the
        # library converts a failed permission check into a 401 access_denied.
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "access_denied")


class MCPEndpointAuthTests(TestCase):
    """Auth gate at the /mcp endpoint."""

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.post(
            "/mcp",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "0"},
                    },
                }
            ),
            content_type="application/json",
            HTTP_ACCEPT="application/json, text/event-stream",
        )
        self.assertIn(response.status_code, (401, 403))

    def test_authenticated_initialize_returns_capabilities(self):
        user = User.objects.create_user(username="mcpinit", password="x")
        self.client.force_login(user)
        response = self.client.post(
            "/mcp",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "0"},
                    },
                }
            ),
            content_type="application/json",
            HTTP_ACCEPT="application/json, text/event-stream",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.get("mcp-session-id"))
        body = response.content.decode("utf-8")
        line = body.split("data: ", 1)[1].strip() if "data: " in body else body
        payload = json.loads(line)
        self.assertEqual(payload.get("jsonrpc"), "2.0")
        self.assertIn("result", payload)
        self.assertIn("tools", payload["result"]["capabilities"])
        # MCP clients render the connector using serverInfo — name + icons
        # decorated in TostiConfig.ready(). Without these the connector
        # shows the generic ru.nl favicon (no longer the case).
        server_info = payload["result"]["serverInfo"]
        self.assertEqual(server_info["name"], "TOSTI")
        self.assertIn("icons", server_info)
        self.assertTrue(server_info["icons"])
        for icon in server_info["icons"]:
            self.assertTrue(icon["src"].startswith("http"))


class ToolAnnotationsAndInstructionsTests(TestCase):
    """Per-tool annotations and server instructions are wired up at startup."""

    def test_read_only_tools_are_marked(self):
        from mcp_server import mcp_server as global_mcp_server

        tools = {t.name: t for t in global_mcp_server._tool_manager.list_tools()}
        for name in (
            "list_venues",
            "list_active_shifts",
            "get_player_state",
            "search_tracks",
        ):
            self.assertIsNotNone(
                tools[name].annotations, f"{name} is missing annotations"
            )
            self.assertTrue(
                tools[name].annotations.readOnlyHint,
                f"{name} should be marked read-only",
            )

    def test_write_tools_are_marked_non_destructive(self):
        from mcp_server import mcp_server as global_mcp_server

        tools = {t.name: t for t in global_mcp_server._tool_manager.list_tools()}
        for name in ("place_order", "request_song", "create_venue_reservation"):
            annotations = tools[name].annotations
            self.assertIsNotNone(annotations, f"{name} is missing annotations")
            self.assertFalse(annotations.readOnlyHint, f"{name} is not read-only")
            self.assertFalse(
                annotations.destructiveHint,
                f"{name} only creates rows; should not be destructive",
            )

    def test_server_instructions_are_populated(self):
        from mcp_server import mcp_server as global_mcp_server

        instructions = global_mcp_server._mcp_server.instructions
        self.assertTrue(instructions)
        self.assertIn("TOSTI", instructions)
        self.assertIn("venue", instructions.lower())


class MCPLandingPageTests(TestCase):
    """Browser-style GETs to /mcp return a human-readable landing page."""

    def test_browser_get_returns_html_landing(self):
        response = self.client.get(
            "/mcp",
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TOSTI MCP server", response.content)
        self.assertEqual(response["Content-Type"].split(";")[0], "text/html")

    def test_mcp_client_get_is_not_intercepted(self):
        response = self.client.get(
            "/mcp",
            HTTP_ACCEPT="application/json, text/event-stream",
        )
        # Falls through to the MCP view, which requires auth.
        self.assertIn(response.status_code, (401, 403, 405))
        if response.status_code != 405:
            self.assertNotIn(b"TOSTI MCP server", response.content)

    def test_missing_accept_header_is_not_intercepted(self):
        response = self.client.get("/mcp")
        # No Accept header → cannot infer "browser"; fall through to MCP view.
        self.assertNotIn(b"TOSTI MCP server", response.content)


class RequireScopeTests(TestCase):
    """``require_scope`` mirrors DRF's IsAuthenticatedOrTokenHasScope semantics."""

    def test_session_request_passes_without_token(self):
        request = _StubRequest(user=User(username="x"), auth=None)
        self.assertIsNone(require_scope(request, "thaliedje:request"))

    def test_token_with_required_scope_passes(self):
        token = MagicMock()
        token.is_valid = MagicMock(return_value=True)
        request = _StubRequest(user=User(username="x"), auth=token)
        self.assertIsNone(require_scope(request, "thaliedje:request"))
        token.is_valid.assert_called_with(["thaliedje:request"])

    def test_token_without_required_scope_returns_error(self):
        token = MagicMock()
        token.is_valid = MagicMock(return_value=False)
        request = _StubRequest(user=User(username="x"), auth=token)
        result = require_scope(request, "orders:order")
        self.assertIsNotNone(result)
        self.assertIn("orders:order", result)
