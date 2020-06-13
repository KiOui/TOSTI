from django import template
from marietje.models import SpotifyQueueItem

register = template.Library()


@register.inclusion_tag("marietje/queue.html")
def render_queue_list(auth, refresh=False, max_items=10):
    """Render queue."""

    queue = SpotifyQueueItem.objects.filter(spotify_settings_object=auth).order_by(
        "-added"
    )[:max_items]
    return {"queue": queue, "refresh": refresh, "auth": auth}
