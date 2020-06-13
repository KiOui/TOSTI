from django import template
from marietje.models import SpotifyQueueItem

register = template.Library()


@register.inclusion_tag("marietje/queue.html")
def render_queue_list(venue, refresh=False, max_items=10):
    """Render queue."""
    if venue.spotify_player is None:
        raise ValueError("No spotify player specified for this venue")
    queue = SpotifyQueueItem.objects.filter(
        spotify_settings_object=venue.spotify_player
    ).order_by("-added")[:max_items]
    return {"queue": queue, "refresh": refresh, "venue": venue}


@register.inclusion_tag("marietje/player.html")
def render_player(venue, refresh=False, controls=False):
    """Render queue."""
    if venue.spotify_player is None:
        raise ValueError("No spotify player specified for this venue")
    return {"refresh": refresh, "venue": venue, "controls": controls}
