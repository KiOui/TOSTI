from django.db import DatabaseError, connection
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import resolve, Resolver404

from tosti.metrics import emit as emit_metric


class HealthCheckMiddleware:
    """Short-circuit `/live` and `/ready` before any other middleware.

    Placed first in MIDDLEWARE so it runs before SecurityMiddleware and
    CommonMiddleware — which means ALLOWED_HOSTS is never checked and the
    probes work regardless of the Host header the caller sends.

    `/live` — liveness: is the process alive? No DB, no cache, no I/O.
    `/ready` — readiness: can the app actually serve traffic? Verifies DB
    connectivity. Fails with 503 if the DB is unreachable.
    """

    LIVE_PATHS = ("/live", "/live/")
    READY_PATHS = ("/ready", "/ready/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in self.LIVE_PATHS:
            return HttpResponse("ok", content_type="text/plain")
        if request.path in self.READY_PATHS:
            return self._ready()
        return self.get_response(request)

    @staticmethod
    def _ready():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            return HttpResponse("db unavailable", content_type="text/plain", status=503)
        return HttpResponse("ok", content_type="text/plain")


class RequestMetricsMiddleware:
    """Emit an `http_request` metric on every request.

    Uses the resolved URL name (not the raw path) to keep metric cardinality
    bounded — a path like `/venues/reservations/123/` would otherwise create
    a new series per ID.

    The `kind` attribute distinguishes three traffic sources:

    - ``page`` — regular Django HTML views (browser page loads).
    - ``api_internal`` — `/api/*` calls authenticated via the session cookie.
      These are this project's own frontend calling its own API.
    - ``api_external`` — `/api/*` calls authenticated via an OAuth2 bearer
      token. These are real third-party API consumers.
    - ``api_anon`` — `/api/*` calls without authentication.
    """

    SKIP_PREFIXES = ("/static/", "/media/", "/live", "/ready")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        path = request.path
        for prefix in self.SKIP_PREFIXES:
            if path.startswith(prefix):
                return response

        try:
            match = resolve(path)
            view = match.view_name or "unresolved"
        except Resolver404:
            view = "unresolved"

        status = response.status_code
        status_class = f"{status // 100}xx"
        authenticated = hasattr(request, "user") and request.user.is_authenticated
        kind = self._classify(path, request, authenticated)

        emit_metric(
            "http_request",
            view=view,
            method=request.method,
            status_class=status_class,
            kind=kind,
            authenticated=authenticated,
        )
        return response

    @staticmethod
    def _classify(path: str, request, authenticated: bool) -> str:
        if not path.startswith("/api/"):
            return "page"
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.lower().startswith("bearer "):
            return "api_external"
        if authenticated:
            return "api_internal"
        return "api_anon"


class MCPLandingMiddleware:
    """Serve a human-readable page when a browser visits ``/mcp``.

    The MCP endpoint speaks JSON-RPC over POST and is meaningless to a
    human pointing their browser at it. Real MCP clients announce
    themselves with ``Accept: application/json, text/event-stream``;
    browsers send ``Accept: text/html, ...``. We branch on that: if the
    request is a GET that prefers HTML, serve a landing page that
    points users at the explainer. Everything else falls through to the
    MCP view.
    """

    MCP_PATHS = ("/mcp", "/mcp/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == "GET"
            and request.path in self.MCP_PATHS
            and self._prefers_html(request)
        ):
            return render(request, "tosti/mcp_landing.html")
        return self.get_response(request)

    @staticmethod
    def _prefers_html(request) -> bool:
        accept = request.META.get("HTTP_ACCEPT", "")
        if not accept:
            return False
        # A browser always lists text/html; MCP clients ask for
        # application/json + text/event-stream and do not include text/html.
        return "text/html" in accept and "text/event-stream" not in accept


class WWWAuthenticateMiddleware:
    """Add ``WWW-Authenticate`` to 401s on OAuth-protected paths.

    RFC 9728 expects an unauthenticated request to a protected resource to
    include a header pointing the client at the resource's metadata document,
    so the client knows where to bootstrap its OAuth2 flow. Without this header
    MCP clients can't auto-discover the auth server.

    DRF's default 401 doesn't carry this header; we add it for /mcp and /api/.
    """

    PROTECTED_PREFIXES = ("/mcp", "/api/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code != 401:
            return response
        if not any(request.path.startswith(p) for p in self.PROTECTED_PREFIXES):
            return response
        # Don't clobber a non-Bearer challenge a downstream view set
        # deliberately (e.g. a Basic-auth route mounted under one of these
        # prefixes). For Bearer challenges (which DRF emits by default) we
        # rewrite the header so the resource_metadata pointer is present —
        # without it, MCP clients can't auto-discover the auth server.
        existing = response.get("WWW-Authenticate", "")
        if existing and not existing.lower().startswith("bearer"):
            return response

        resource_metadata = request.build_absolute_uri(
            "/.well-known/oauth-protected-resource"
        )
        response["WWW-Authenticate"] = (
            f'Bearer realm="tosti", resource_metadata="{resource_metadata}"'
        )
        return response
