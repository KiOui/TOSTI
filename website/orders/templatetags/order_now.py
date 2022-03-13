from django import template
from django.utils import timezone

from orders.models import Shift, OrderVenue

register = template.Library()


@register.inclusion_tag("orders/order_now_button.html", takes_context=True)
def render_order_now_button(context, shift=None, venue=None):
    """Render order now button."""
    if shift:
        return {"shift": shift, "request": context.get("request")}
    elif venue:
        return {"venue": venue, "request": context.get("request")}


@register.inclusion_tag("orders/place_order_button.html", takes_context=True)
def render_place_order_button(context, shift):
    """Render order now button."""
    has_order_perm = context[
        "request"
    ].user in shift.venue.get_users_with_order_perms() and shift.user_can_order_amount(context["request"].user, 1)
    return {"shift": shift, "has_order_perm": has_order_perm}


@register.inclusion_tag("orders/order_now_buttons_shifts.html", takes_context=True)
def render_order_now_buttons_active_shifts(context, shifts=None):
    """Render order now buttons for all active shifts."""
    if shifts is None:
        shifts = Shift.objects.filter(
            start__lte=timezone.now(), end__gte=timezone.now(), finalized=False
        ).order_by("start", "venue__venue__name")

    buttons = [{"shift": x} for x in shifts]

    return {"shifts": buttons, "request": context.get("request")}


@register.inclusion_tag("orders/order_now_buttons_shifts.html", takes_context=True)
def render_order_now_buttons_can_order(context):
    """Render order now buttons for all shifts accepting orders."""
    shifts = Shift.objects.filter(
        start__lte=timezone.now(), end__gte=timezone.now(), can_order=True
    ).order_by("start", "venue__venue__name")

    buttons = [{"shift": x} for x in shifts]

    return {"shifts": buttons, "request": context.get("request")}


@register.inclusion_tag("orders/order_buttons_for_venues.html", takes_context=True)
def render_order_now_buttons_venues(context):
    """Render order now buttons for all active shifts."""
    venues = OrderVenue.objects.filter(venue__active=True).order_by("venue__name")

    buttons = [{"venue": x} for x in venues]

    return {"venues": buttons, "request": context.get("request")}
