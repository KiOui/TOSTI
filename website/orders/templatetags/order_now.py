from django import template
from django.utils import timezone

from orders.models import Shift
from venues.models import Venue

register = template.Library()


@register.inclusion_tag("orders/order_header.html")
def render_order_header(shift):
    """Render order header."""
    return {"shift": shift}


@register.inclusion_tag("orders/order_now.html")
def render_order_now_button(shift):
    """Render order now button."""
    return {"shift": shift}


@register.inclusion_tag("orders/order_now.html")
def render_order_now_buttons_active_shifts(shifts=None):
    """Render order now buttons for all active shifts."""
    if shifts is None:
        shifts = Shift.objects.filter(
            start_date__lte=timezone.now(), end_date__gte=timezone.now(),
        ).order_by("start_date", "venue__name")

    buttons = [{"shift": x} for x in shifts]

    return {"shifts": buttons}


@register.inclusion_tag("orders/order_now.html")
def render_order_now_buttons_can_order():
    """Render order now buttons for all shifts accepting orders."""
    shifts = Shift.objects.filter(
        start_date__lte=timezone.now(), end_date__gte=timezone.now(), can_order=True
    ).order_by("start_date", "venue__name")

    buttons = [{"shift": x} for x in shifts]

    return {"shifts": buttons}


@register.inclusion_tag("orders/order_now_at.html")
def render_order_now_buttons_venues():
    """Render order now buttons for all active shifts."""
    venues = Venue.objects.filter(active=True).order_by("name")

    buttons = [{"venue": x} for x in venues]

    return {"venues": buttons}


@register.filter
def currently_active_shift_for_venue(venue):
    """Get the currently active shift for a venue (if it exists)."""
    return venue.shift_set.filter(
        start_date__lte=timezone.now(), end_date__gte=timezone.now()
    ).first()
