"""
OAuth2 / RFC discovery and dynamic client registration views.

These views support MCP clients (and any other RFC-compliant OAuth2 client) that
expect to:

  - Discover authorization-server metadata at ``.well-known/oauth-authorization-server``
    (RFC 8414).
  - Discover protected-resource metadata at ``.well-known/oauth-protected-resource``
    (RFC 9728), so the client knows which authorization server protects ``/mcp``
    and ``/api/v1/``.
  - Self-register a client at ``/oauth/register/`` (RFC 7591), so the user
    doesn't have to manually create an OAuth Application.
"""

import json

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.models import Application
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.views import AuthorizationView

from tosti.forms import GranularAuthorizationForm

# Per-IP registration cap: protects the Application table from a flood of
# self-registered clients. Tuned generously for a normal MCP client doing one
# registration per install.
_DCR_RATE_LIMIT_KEY = "tosti:dcr:{}"
_DCR_RATE_LIMIT_PER_HOUR = 10


def _absolute(request, name: str) -> str:
    return request.build_absolute_uri(reverse(name))


class OAuthAuthorizationServerMetadataView(View):
    """RFC 8414 OAuth 2.0 Authorization Server Metadata."""

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        base = request.build_absolute_uri("/").rstrip("/")
        scopes = list(get_scopes_backend().get_all_scopes().keys())
        data = {
            "issuer": base,
            "authorization_endpoint": _absolute(request, "oauth2_provider:authorize"),
            "token_endpoint": _absolute(request, "oauth2_provider:token"),
            "revocation_endpoint": _absolute(request, "oauth2_provider:revoke-token"),
            "introspection_endpoint": _absolute(request, "oauth2_provider:introspect"),
            "registration_endpoint": _absolute(
                request, "oauth-dynamic-client-registration"
            ),
            "scopes_supported": scopes,
            # RFC 8414 metadata reflects the *recommended* surface for new
            # clients, not everything the underlying library can serve:
            # - implicit / password are deprecated by OAuth 2.1 — never
            #   advertised, even though django-oauth-toolkit still accepts
            #   them. (Swagger UI uses implicit internally; that's
            #   independent of what we tell external clients.)
            # - client_credentials is intentionally NOT advertised either:
            #   server-to-server access is a maintainer-issued exception
            #   (confidential client provisioned out of band), not a path
            #   we want third parties to discover and try. Discovery only
            #   advertises the authorization_code + refresh_token flow.
            "response_types_supported": ["code"],
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
            ],
            # Only token-endpoint methods relevant to the public flow:
            # public clients (DCR, account-page registration) authenticate
            # with ``none`` + PKCE. ``client_secret_basic`` /
            # ``client_secret_post`` are still accepted by the library for
            # maintainer-issued confidential clients but aren't advertised
            # — see the grant_types_supported comment above.
            "token_endpoint_auth_methods_supported": ["none"],
            # Only S256 is advertised; PKCE best practice (RFC 7636 §4.2)
            # mandates S256 whenever the client can compute it. The library
            # still accepts ``plain`` if a client insists.
            "code_challenge_methods_supported": ["S256"],
        }
        return JsonResponse(data)


class OAuthProtectedResourceMetadataView(View):
    """RFC 9728 OAuth 2.0 Protected Resource Metadata.

    Tells clients which authorization server protects this resource. Served at
    ``.well-known/oauth-protected-resource``.
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        base = request.build_absolute_uri("/").rstrip("/")
        data = {
            "resource": base,
            "authorization_servers": [base],
            "scopes_supported": list(get_scopes_backend().get_all_scopes().keys()),
            "bearer_methods_supported": ["header"],
        }
        return JsonResponse(data)


@method_decorator(csrf_exempt, name="dispatch")
class DynamicClientRegistrationView(View):
    """RFC 7591 OAuth 2.0 Dynamic Client Registration.

    MCP clients POST a JSON document here to
    self-register. We always provision:
      - a public client (no client_secret returned)
      - authorization-code grant only
      - PKCE required (enforced globally by django-oauth-toolkit's PKCE_REQUIRED)
      - scopes restricted to the intersection of what the client asks for and
        what TOSTI publishes

    Per-IP rate limit prevents flooding the Application table.
    """

    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        """Serve a human-readable landing page for browser visits.

        The actual DCR happens over POST; humans who paste the URL into
        their browser get a friendly explainer pointing at the docs
        instead of a 405. Non-browser GETs (which don't ask for HTML)
        get the conventional 405 so RFC 7591 clients see expected
        behaviour.
        """
        accept = request.META.get("HTTP_ACCEPT", "")
        if "text/html" not in accept:
            return HttpResponseNotAllowed(["POST"])
        return render(request, "tosti/oauth_register_landing.html")

    def post(self, request, *args, **kwargs):
        ip = self._client_ip(request)
        cache_key = _DCR_RATE_LIMIT_KEY.format(ip)
        count = cache.get(cache_key, 0)
        if count >= _DCR_RATE_LIMIT_PER_HOUR:
            return JsonResponse(
                {
                    "error": "rate_limited",
                    "error_description": (
                        "Too many client registrations from this IP recently."
                    ),
                },
                status=429,
            )

        try:
            # UnicodeDecodeError is a subclass of ValueError, as is
            # json.JSONDecodeError; ValueError catches both.
            body_text = request.body.decode("utf-8") or "{}"
            payload = json.loads(body_text)
        except ValueError:
            return HttpResponseBadRequest(
                json.dumps(
                    {
                        "error": "invalid_client_metadata",
                        "error_description": "Body must be JSON.",
                    }
                ),
                content_type="application/json",
            )

        redirect_uris = payload.get("redirect_uris") or []
        if not isinstance(redirect_uris, list) or not redirect_uris:
            return JsonResponse(
                {
                    "error": "invalid_redirect_uri",
                    "error_description": "redirect_uris must be a non-empty list.",
                },
                status=400,
            )
        for uri in redirect_uris:
            if not isinstance(uri, str) or not uri:
                return JsonResponse(
                    {
                        "error": "invalid_redirect_uri",
                        "error_description": "Each redirect URI must be a string.",
                    },
                    status=400,
                )
            scheme = uri.split(":", 1)[0].lower()
            allowed = settings.OAUTH2_PROVIDER.get(
                "ALLOWED_REDIRECT_URI_SCHEMES", ["https"]
            )
            if scheme not in allowed:
                return JsonResponse(
                    {
                        "error": "invalid_redirect_uri",
                        "error_description": (
                            f"Redirect URI scheme '{scheme}' is not allowed. "
                            f"Allowed: {sorted(allowed)}."
                        ),
                    },
                    status=400,
                )

        # Restrict requested scopes to the intersection of what the client asks
        # for and what TOSTI publishes. RFC 7591 says to silently issue the
        # subset the server is willing to grant.
        requested_scope = (payload.get("scope") or "").split()
        all_scopes = set(get_scopes_backend().get_all_scopes().keys())
        granted_scope = (
            [s for s in requested_scope if s in all_scopes]
            if requested_scope
            else ["read"]
        )

        client_name = (
            payload.get("client_name")
            or payload.get("software_id")
            or "Dynamically registered MCP client"
        )[:255]

        application = Application.objects.create(
            name=client_name,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris=" ".join(redirect_uris),
            user=None,
            skip_authorization=False,
        )

        cache.set(cache_key, count + 1, timeout=3600)

        # Public clients do not get a usable client_secret. We still return
        # ``None`` per RFC 7591 to make the response shape predictable.
        return JsonResponse(
            {
                "client_id": application.client_id,
                "client_id_issued_at": int(application.created.timestamp()),
                "client_secret": None,
                "client_name": application.name,
                "redirect_uris": redirect_uris,
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": " ".join(granted_scope),
            },
            status=201,
        )

    @staticmethod
    def _client_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")


class GranularAuthorizationView(AuthorizationView):
    """Consent screen that lets the user grant a subset of requested scopes.

    Swaps the upstream all-or-nothing ``AllowForm`` (whose ``scope`` is a
    hidden string) for ``GranularAuthorizationForm`` (one checkbox per
    requested scope). RFC 6749 §3.3 explicitly allows the authorization
    server to issue a narrower scope than requested, so this is a
    conforming refinement.

    Everything else (PKCE, ``code_challenge`` round-trip, the
    ``approval_prompt=auto`` short-circuit, the ``state``/``nonce``
    plumbing) is inherited unchanged from ``AuthorizationView``.
    """

    form_class = GranularAuthorizationForm
