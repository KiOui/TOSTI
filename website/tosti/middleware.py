from django.db import DatabaseError, connection
from django.http import HttpResponse
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
