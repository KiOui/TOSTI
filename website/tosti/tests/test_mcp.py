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
from django.test import RequestFactory, TestCase
from django.urls import reverse
from oauth2_provider.models import Application

from tosti.mcp import require_scope
from tosti.middleware import WWWAuthenticateMiddleware

User = get_user_model()


class _StubRequest:
    """Lightweight stand-in for a Django request inside a tool method."""

    def __init__(self, user, auth=None):
        self.user = user
        self.auth = auth


class OAuthDiscoveryTests(TestCase):
    """RFC 8414 / RFC 9728 discovery endpoints."""

    def test_authorization_server_metadata_has_required_fields(self):
        response = self.client.get(reverse("oauth-authorization-server-metadata"))
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
        for scope in ("read", "write", "orders:order", "thaliedje:request"):
            self.assertIn(scope, data["scopes_supported"])

    def test_authorization_server_metadata_does_not_advertise_deprecated_grants(self):
        response = self.client.get(reverse("oauth-authorization-server-metadata"))
        data = json.loads(response.content)
        # OAuth 2.1 deprecates implicit and password; do not advertise them
        # even though the underlying library still serves them.
        self.assertNotIn("implicit", data["grant_types_supported"])
        self.assertNotIn("password", data["grant_types_supported"])
        self.assertNotIn("token", data["response_types_supported"])
        # PKCE best practice: only S256.
        self.assertEqual(data["code_challenge_methods_supported"], ["S256"])

    def test_authorization_server_metadata_advertises_registration_endpoint(self):
        response = self.client.get(reverse("oauth-authorization-server-metadata"))
        data = json.loads(response.content)
        self.assertTrue(data["registration_endpoint"].endswith("/oauth/register/"))

    def test_protected_resource_metadata_returns_required_fields(self):
        response = self.client.get(reverse("oauth-protected-resource-metadata"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("resource", data)
        self.assertIn("authorization_servers", data)
        self.assertIn("scopes_supported", data)
        self.assertEqual(data["bearer_methods_supported"], ["header"])


class WWWAuthenticateHeaderTests(TestCase):
    """Unauthenticated requests to /mcp and /api/ point at the resource metadata."""

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

    def test_non_bearer_challenge_is_preserved(self):
        """A non-Bearer challenge from a downstream view must not be overwritten."""
        from django.http import HttpResponse

        def view(_request):
            r = HttpResponse(status=401)
            r["WWW-Authenticate"] = 'Basic realm="admin"'
            return r

        middleware = WWWAuthenticateMiddleware(view)
        request = RequestFactory().get("/api/v1/some-protected/")
        response = middleware(request)
        self.assertEqual(response["WWW-Authenticate"], 'Basic realm="admin"')


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
        self.assertEqual(
            response._csp_update, {"form-action": ["https:"]}
        )


class DynamicClientRegistrationTests(TestCase):
    """RFC 7591 dynamic client registration."""

    def setUp(self):
        cache.clear()

    def _post(self, payload):
        return self.client.post(
            reverse("oauth-dynamic-client-registration"),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_minimum_valid_payload_creates_application(self):
        response = self._post({"redirect_uris": ["https://example.com/callback"]})
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        self.assertIn("client_id", body)
        self.assertIsNone(body["client_secret"])
        self.assertEqual(body["token_endpoint_auth_method"], "none")
        self.assertEqual(body["redirect_uris"], ["https://example.com/callback"])
        self.assertIn("scope", body)
        # The application is persisted as a public auth-code client.
        app = Application.objects.get(client_id=body["client_id"])
        self.assertEqual(app.client_type, Application.CLIENT_PUBLIC)
        self.assertEqual(
            app.authorization_grant_type, Application.GRANT_AUTHORIZATION_CODE
        )

    def test_disallowed_redirect_scheme_is_rejected(self):
        response = self._post({"redirect_uris": ["javascript:alert(1)"]})
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_redirect_uri")

    def test_missing_redirect_uris_is_rejected(self):
        response = self._post({})
        self.assertEqual(response.status_code, 400)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "invalid_redirect_uri")

    def test_unknown_scopes_are_filtered_out(self):
        response = self._post(
            {
                "redirect_uris": ["https://example.com/cb"],
                "scope": "read thaliedje:request not-a-scope",
            }
        )
        self.assertEqual(response.status_code, 201)
        body = json.loads(response.content)
        granted = set(body["scope"].split())
        self.assertEqual(granted, {"read", "thaliedje:request"})

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
            reverse("oauth-dynamic-client-registration"),
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dynamic client registration", response.content)
        self.assertEqual(response["Content-Type"].split(";")[0], "text/html")

    def test_non_browser_get_returns_405(self):
        response = self.client.get(
            reverse("oauth-dynamic-client-registration"),
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 405)

    def test_invalid_json_is_rejected(self):
        response = self.client.post(
            reverse("oauth-dynamic-client-registration"),
            data="this is not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_rate_limit_kicks_in(self):
        for _ in range(10):
            response = self._post({"redirect_uris": ["https://example.com/cb"]})
            self.assertEqual(response.status_code, 201)
        response = self._post({"redirect_uris": ["https://example.com/cb"]})
        self.assertEqual(response.status_code, 429)
        body = json.loads(response.content)
        self.assertEqual(body["error"], "rate_limited")


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
