from django import template
from marietje.models import SpotifyQueueItem

register = template.Library()


@register.inclusion_tag("marietje/queue.html")
def render_queue_list(spotify, refresh=False, max_items=10):
    """Render queue."""
    queue = SpotifyQueueItem.objects.filter(spotify_settings_object=spotify).order_by(
        "-added"
    )[:max_items]
    return {"queue": queue, "refresh": refresh, "spotify": spotify}


@register.inclusion_tag("marietje/player.html")
def render_player(spotify, refresh=False, controls=False):
    """Render queue."""
    return {"refresh": refresh, "spotify": spotify, "controls": controls}
