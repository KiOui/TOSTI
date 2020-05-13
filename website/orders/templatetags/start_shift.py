import pytz
from django import template
from django.conf import settings
from django.utils.datetime_safe import datetime

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
    timezone = pytz.timezone(settings.TIME_ZONE)
    today = timezone.localize(datetime.now())
    start = timezone.localize(datetime(today.year, today.month, today.day))

    if venue.shift_set.filter(start_date__lte=today, end_date__gte=today).exists():
        return venue.shift_set.filter(
            start_date__lte=today, end_date__gte=today
        ).first()
    elif venue.shift_set.filter(start_date__gte=start).exists():
        return venue.shift_set.filter(start_date__gte=start).first()
    else:
        return None
