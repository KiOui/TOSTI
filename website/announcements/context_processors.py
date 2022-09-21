from .models import Announcement


def announcements(request):
    """Get a list of all active announcements."""
    closed_announcements = request.session.get("closed_announcements", [])
    announcements_list = [a for a in Announcement.objects.all() if a.is_visible and a.pk not in closed_announcements]
    return {"announcements": announcements_list}
