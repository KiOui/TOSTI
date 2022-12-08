import json
import urllib.parse

from announcements.models import Announcement


def sanitize_closed_announcements(closed_announcements) -> list:
    """Convert a cookie (closed_announcements) to a list of id's of closed announcements."""
    if closed_announcements is None or type(closed_announcements) != str:
        return []
    try:
        closed_announcements_list = json.loads(urllib.parse.unquote(closed_announcements))
    except json.JSONDecodeError:
        return []

    if type(closed_announcements_list) != list:
        return []

    closed_announcements_list_ints = []
    for closed_announcement in closed_announcements_list:
        if type(closed_announcement) == int:
            closed_announcements_list_ints.append(closed_announcement)
    return closed_announcements_list_ints


def validate_closed_announcements(closed_announcements) -> list:
    """Verify the integers in the list such that the ID's that in the database exist only remain."""
    return list(Announcement.objects.filter(id__in=closed_announcements).values_list("id", flat=True))


def encode_closed_announcements(closed_announcements: list) -> str:
    """Encode the announcement list in URL encoding."""
    return urllib.parse.quote(json.dumps(closed_announcements))
