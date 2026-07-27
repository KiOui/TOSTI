"""
TOSTI-specific customisations on top of django-oauth-toolkit's OAuth2 stack.

django-oauth-toolkit 3.4.0 ships the RFC 8414 authorization-server metadata
view, the RFC 9728 protected-resource metadata view, and the RFC 7591/7592
Dynamic Client Registration views. We defer to those. This module only holds
what the library does not cover:

  - :class:`GranularAuthorizationView` — replaces the all-or-nothing consent
    form with one checkbox per requested scope.
  - :class:`RateLimitedAnonymousDCRPermission` — DCR permission class that
    keeps the endpoint anonymous (so MCP clients can bootstrap without a
    login) but caps registrations per IP.
  - :class:`DCRLandingView` — HTML explainer served on browser GETs to
    ``/oauth/register/``; POSTs and non-HTML GETs are proxied to the
    library's DCR view unchanged.
"""

from django.core.cache import cache
from django.shortcuts import render
from django.views import View
from oauth2_provider.views import AuthorizationView, DynamicClientRegistrationView

from tosti.forms import GranularAuthorizationForm

# Per-IP registration cap: protects the Application table from a flood of
# self-registered clients. Tuned generously for a normal MCP client doing one
# registration per install.
_DCR_RATE_LIMIT_KEY = "tosti:dcr:{}"
_DCR_RATE_LIMIT_PER_HOUR = 10


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class RateLimitedAnonymousDCRPermission:
    """DCR permission class: anonymous, rate-limited per client IP.

    The library's default ``IsAuthenticatedDCRPermission`` requires a
    session-authenticated user, which breaks the MCP bootstrap flow —
    Claude Desktop et al. self-register anonymously before they have any
    credentials at all. We allow anonymous POSTs but cap them per IP so a
    misbehaving client (or a scanner) cannot flood the ``Application``
    table.
    """

    def has_permission(self, request) -> bool:
        ip = _client_ip(request)
        cache_key = _DCR_RATE_LIMIT_KEY.format(ip)
        count = cache.get(cache_key, 0)
        if count >= _DCR_RATE_LIMIT_PER_HOUR:
            return False
        cache.set(cache_key, count + 1, timeout=3600)
        return True


class DCRLandingView(View):
    """Wrap the library DCR view with an HTML explainer for browsers.

    The library's ``DynamicClientRegistrationView`` speaks JSON only and
    returns 405 on GET. Real MCP clients POST; humans who paste the URL
    into their browser get a friendly landing page pointing at the docs.
    Non-browser GETs and all POSTs fall through to the library view
    unchanged.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET" and "text/html" in request.META.get(
            "HTTP_ACCEPT", ""
        ):
            return render(request, "tosti/oauth_register_landing.html")
        return DynamicClientRegistrationView.as_view()(request, *args, **kwargs)


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
