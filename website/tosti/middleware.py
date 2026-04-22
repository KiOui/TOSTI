from django.db import DatabaseError, connection
from django.http import HttpResponse


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
