from django import template
from django.utils import timezone

from orders.services import user_can_manage_shifts_in_venue
from thaliedje.models import Player
from orders.models import OrderVenue

register = template.Library()


@register.inclusion_tag("tosti/venue_card.html", takes_context=True)
def render_venue_card(context, shift=None, venue=None, show_player=True, show_venue_reservation=True):
    """Render venue card."""
    if shift and venue is None:
        venue = shift.venue

    return {
        "venue": venue,
        "show_venue_reservation": show_venue_reservation,
        "venue_reservation": venue.venue.reservations.filter(
            accepted=True, start__lte=timezone.now(), end__gte=timezone.now()
        ).first()
        or None,
        "request": context.get("request"),
        "admin": (venue and user_can_manage_shifts_in_venue(context["request"].user, venue))
        or (shift and user_can_manage_shifts_in_venue(context["request"].user, shift.venue)),
        "show_player": show_player and Player.get_player(venue.venue) is not None,
    }


@register.inclusion_tag("tosti/venue_cards_for_venues.html", takes_context=True)
def render_venue_cards_venues(context):
    """Render order now buttons for all active shifts."""
    venues = OrderVenue.objects.filter(venue__active=True).order_by("venue__name")

    buttons = [{"venue": x} for x in venues]

    return {"venues": buttons, "request": context.get("request")}
