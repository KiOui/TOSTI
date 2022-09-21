from django import template
from django.db.models import Q
from django.utils import timezone

from announcements.models import Announcement

register = template.Library()


@register.inclusion_tag("announcements/announcements.html")
def render_announcements():
    """Render all active announcements."""
    return {
        "announcements": Announcement.objects.filter(
            (Q(until__gt=timezone.now()) | Q(until=None)) & Q(since__lte=timezone.now())
        )
    }
