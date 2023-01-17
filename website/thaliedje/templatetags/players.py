from django import template

from thaliedje.models import Player, SpotifyPlayer

register = template.Library()


@register.inclusion_tag("thaliedje/requests.html")
def render_requests(player, show_requestor=True):
    """Render queue."""
    return {"player": player, "show_requestor": show_requestor}


@register.inclusion_tag("thaliedje/queue.html")
def render_queue(player):
    """Render queue."""
    return {"player": player}


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
    """
    Render all players in card format.

    :param context: needed because the render_player must know the request
    :return: a dictionary
    """
    return {"players": Player.objects.all(), "request": context["request"]}


@register.inclusion_tag("thaliedje/render_player_card.html", takes_context=True)
def render_player_card(context, player):
    """Render a player in card format."""
    return {"player": player, "request": context["request"]}
