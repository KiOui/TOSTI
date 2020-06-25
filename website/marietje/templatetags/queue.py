from django import template
from marietje.models import SpotifyQueueItem, SpotifyAccount

register = template.Library()


@register.inclusion_tag("marietje/queue.html")
def render_queue_list(spotify_account, refresh=False, max_items=10):
    """Render queue."""
    queue = SpotifyQueueItem.objects.filter(
        spotify_settings_object=spotify_account
    ).order_by("-added")[:max_items]
    return {"queue": queue, "refresh": refresh, "spotify": spotify_account}


@register.inclusion_tag("marietje/player.html", takes_context=True)
def render_player(context, spotify_account, refresh=False):
    """Render queue."""
    return {
        "refresh": refresh,
        "spotify": spotify_account,
        "controls": True if context["request"].user.is_staff else False,
    }


@register.inclusion_tag("marietje/player.html", takes_context=True)
def render_venue_player(context, venue, refresh=False):
    """Render queue."""
    player = SpotifyAccount.get_player(venue)
    return {
        "refresh": refresh,
        "spotify": player,
        "controls": True if context["request"].user.is_staff else False,
    }
