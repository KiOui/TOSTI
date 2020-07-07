from django import template
from django.utils import timezone

from orders.models import Shift, OrderVenue

register = template.Library()


@register.inclusion_tag("orders/shift_header.html", takes_context=True)
def render_order_header(context, shift, refresh=False):
    """Render order header."""
    return {"shift": shift, "refresh": refresh, "request": context.get("request")}


@register.inclusion_tag("orders/admin_footer.html", takes_context=True)
def render_admin_footer(context, shift, refresh=False):
    """Render order footer."""
    has_change_order_permissions = context["request"].user in shift.get_users_with_change_perms()
    return {
        "shift": shift,
        "refresh": refresh,
        "request": context.get("request"),
        "has_change_order_permissions": has_change_order_permissions,
    }


@register.inclusion_tag("orders/shift_orders.html", takes_context=True)
def render_order_items(context, shift, refresh=False, admin=False, user=None):
    """Render order items."""
    return {"shift": shift, "refresh": refresh, "admin": admin, "user": user, "request": context.get("request")}


@register.inclusion_tag("orders/shift_summary.html", takes_context=True)
def render_item_overview(context, shift, refresh=False):
    """Render item overview."""
    return {"shift": shift, "refresh": refresh, "request": context.get("request")}


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
        shifts = Shift.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now(),).order_by(
            "start_date", "venue__venue__name"
        )

    buttons = [{"shift": x} for x in shifts]

    return {"shifts": buttons, "request": context.get("request")}


@register.inclusion_tag("orders/order_now_buttons_shifts.html", takes_context=True)
def render_order_now_buttons_can_order(context):
    """Render order now buttons for all shifts accepting orders."""
    shifts = Shift.objects.filter(
        start_date__lte=timezone.now(), end_date__gte=timezone.now(), can_order=True
    ).order_by("start_date", "venue__venue__name")

    buttons = [{"shift": x} for x in shifts]

    return {"shifts": buttons, "request": context.get("request")}


@register.inclusion_tag("orders/order_buttons_for_venues.html", takes_context=True)
def render_order_now_buttons_venues(context):
    """Render order now buttons for all active shifts."""
    venues = OrderVenue.objects.filter(venue__active=True).order_by("venue__name")

    buttons = [{"venue": x} for x in venues]

    return {"venues": buttons, "request": context.get("request")}


@register.filter
def currently_active_shift_for_venue(venue):
    """Get the currently active shift for a venue (if it exists)."""
    return (
        venue.shift_set.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())
        .order_by("end_date")
        .first()
    )
