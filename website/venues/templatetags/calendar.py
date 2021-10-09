from django import template

from ..models import Venue

register = template.Library()


@register.inclusion_tag("venues/venue_calendar.html", takes_context=True)
def render_venue_calendar(context, venue: Venue = None):
    """Render venue calendar."""
    return {"venue": venue, "request": context.get("request")}


@register.inclusion_tag("venues/all_venues_calendar.html", takes_context=True)
def render_calendar(context):
    """Render venue calendar."""
    return {"request": context.get("request")}
