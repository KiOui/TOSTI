from announcements.services import (
    validate_closed_announcements,
    sanitize_closed_announcements,
    encode_closed_announcements,
)
from django.apps import apps


class ClosedAnnouncementsMiddleware:
    """Closed Announcements Middleware."""

    def __init__(self, get_response):
        """Initialize."""
        self.get_response = get_response

    def __call__(self, request):
        """Update the closed announcements' cookie."""
        response = self.get_response(request)

        closed_announcements = validate_closed_announcements(
            sanitize_closed_announcements(request.COOKIES.get("closed-announcements", None))
        )
        response.set_cookie("closed-announcements", encode_closed_announcements(closed_announcements))

        return response


class AppAnnouncementMiddleware:
    """Announcement Middleware."""

    def __init__(self, get_response):
        """Initialize Announcement Middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Call app announcement function if they exist for gathering all announcements."""
        announcements = []
        for app in apps.get_app_configs():
            if hasattr(app, "announcements") and hasattr(app.announcements, "__call__"):
                announcements += app.announcements(request)
        setattr(request, "_app_announcements", announcements)

        return self.get_response(request)
