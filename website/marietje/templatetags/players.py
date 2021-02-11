from django import template

from marietje.models import Player

register = template.Library()


@register.inclusion_tag("marietje/queue.html")
def render_queue_list(player):
    """Render queue."""
    return {"player": player}


@register.inclusion_tag("marietje/player.html", takes_context=True)
def render_player(context, player):
    """Render queue."""
    return {
        "player": player,
        "controls": context["request"].user in player.get_users_with_control_permissions(),
    }


@register.inclusion_tag("marietje/player.html", takes_context=True)
def render_venue_player(context, venue):
    """Render queue."""
    player = Player.get_player(venue)
    return {
        "player": player,
        "controls": context["request"].user in player.get_users_with_control_permissions(),
    }


@register.inclusion_tag("marietje/render_players.html", takes_context=True)
def render_players(context):
    """
    Render all players in card format.

    :param context: needed because the render_player must know the request
    :return: a dictionary
    """
    return {"players": Player.objects.all(), "request": context["request"]}


@register.inclusion_tag("marietje/render_player_card.html", takes_context=True)
def render_player_card(context, player):
    """Render a player in card format."""
    return {"player": player, "request": context["request"]}
