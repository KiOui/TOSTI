from django import template

from thaliedje.models import Player, SpotifyPlayer

register = template.Library()


@register.inclusion_tag("thaliedje/requests.html")
def render_requests(player, show_requestor=True):
    """Render queue."""
    return {"player": player, "show_requestor": show_requestor}


@register.inclusion_tag("thaliedje/queue.html", takes_context=True)
def render_queue(context, player):
    """Render the (enriched) queue.

    ``show_requestor`` is gated on authentication: the public queue view
    deliberately redacts requestor identity for anonymous viewers (the
    API view mirrors this), matching the privacy policy and the existing
    ``AnonymousRequestedQueueItemSerializer`` behaviour.
    """
    user = context["request"].user if "request" in context else None
    return {
        "player": player,
        "show_requestor": bool(user and user.is_authenticated),
    }


@register.inclusion_tag("thaliedje/player.html", takes_context=True)
def render_player(context, player):
    """Render player."""
    try:
        player = SpotifyPlayer.objects.get(id=player.id)
    except SpotifyPlayer.DoesNotExist:
        controls = False
    else:
        controls = player.can_control(context["request"].user)
    return {"player": player, "controls": controls}


@register.inclusion_tag("thaliedje/player.html", takes_context=True)
def render_venue_player(context, venue):
    """Render player for a venue."""
    player = Player.get_player(venue)
    return render_player(context, player)


@register.inclusion_tag("thaliedje/render_players.html", takes_context=True)
def render_players(context):
    """Render all players in card format.

    :param context: needed because the render_player must know the request
    :return: a dictionary
    """
    players = list(Player.objects.all().select_subclasses())
    return {"players": players, "request": context["request"]}


@register.inclusion_tag("thaliedje/render_player_card.html", takes_context=True)
def render_player_card(context, player):
    """Render a player in card format."""
    return {"player": player, "request": context["request"]}
