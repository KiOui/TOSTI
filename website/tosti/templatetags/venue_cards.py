from django import template

from thaliedje.models import Player
from orders.models import OrderVenue

register = template.Library()


@register.inclusion_tag("tosti/venue_card.html", takes_context=True)
def render_venue_card(context, shift=None, venue=None, show_player=True):
    """Render venue card."""
    if shift and venue is None:
        venue = shift.venue

    return {
        "venue": venue,
        "request": context.get("request"),
        "admin": context["request"].user in venue.get_users_with_shift_admin_perms(),
        "show_player": show_player and Player.get_player(venue.venue) is not None,
    }


@register.inclusion_tag("tosti/venue_cards_for_venues.html", takes_context=True)
def render_venue_cards_venues(context):
    """Render order now buttons for all active shifts."""
    venues = OrderVenue.objects.filter(venue__active=True).order_by("venue__name")

    buttons = [{"venue": x} for x in venues]

    return {"venues": buttons, "request": context.get("request")}
