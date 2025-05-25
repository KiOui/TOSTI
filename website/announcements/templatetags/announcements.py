from django import template
from django.db.models import Q

from announcements.models import Announcement
from announcements.services import sanitize_closed_announcements

register = template.Library()


@register.inclusion_tag("announcements/announcements.html", takes_context=True)
def render_announcements(context):
    """Render all active announcements."""
    request = context.get("request")
    closed_announcements = sanitize_closed_announcements(
        request.COOKIES.get("closed-announcements", None)
    )

    return {
        "announcements": Announcement.objects.visible().filter(
            ~Q(id__in=closed_announcements)
        ),
        "app_announcements": getattr(request, "_app_announcements", []),
        "closed_announcements": closed_announcements,
    }
