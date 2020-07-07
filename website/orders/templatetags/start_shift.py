import pytz
from django import template
from django.conf import settings
from django.utils.datetime_safe import datetime

from orders.models import OrderVenue

register = template.Library()


@register.inclusion_tag("orders/start_shift.html", takes_context=True)
def render_start_shift_buttons(context, venues=None):
    """Render start shift buttons."""
    if venues is None:
        venues = OrderVenue.objects.filter(venue__active=True).order_by("venue__name")

    buttons = [{"venue": x} for x in venues if context["request"].user in x.get_users_with_shift_admin_perms()]

    return {"venues": buttons}


@register.filter
def currently_active_shift_for_venue(venue):
    """Get the currently active shift for a venue (if it exists)."""
    timezone = pytz.timezone(settings.TIME_ZONE)
    today = timezone.localize(datetime.now())
    start = timezone.localize(datetime(today.year, today.month, today.day))

    if venue.shift_set.filter(start_date__lte=today, end_date__gte=today).exists():
        return venue.shift_set.filter(start_date__lte=today, end_date__gte=today).first()
    elif venue.shift_set.filter(start_date__gte=start).exists():
        return venue.shift_set.filter(start_date__gte=start).first()
    else:
        return None
