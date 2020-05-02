from django import template
from django.utils import timezone

from venues.models import Venue

register = template.Library()


@register.inclusion_tag("orders/start_shift.html")
def render_start_shift_buttons(venues=None):
    """Render start shift buttons."""
    if venues is None:
        venues = Venue.objects.filter(active=True).order_by("name")

    buttons = [{"venue": x} for x in venues]

    return {"venues": buttons}


@register.filter
def currently_active_shift_for_venue(venue):
    """Get the currently active shift for a venue (if it exists)."""
    return venue.shift_set.filter(
        start_date__lte=timezone.now(), end_date__gte=timezone.now()
    ).first()
