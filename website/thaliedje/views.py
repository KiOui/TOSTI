from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Player

COOKIE_CLIENT_ID = "client_id"


class IndexView(TemplateView):
    """Index view for thaliedje."""

    template_name = "thaliedje/index.html"

    def get(self, request, **kwargs):
        """GET an overview of all players."""
        return render(request, self.template_name)


class NowPlayingView(TemplateView):
    """Now playing view with the player for a venue."""

    template_name = "thaliedje/now_playing.html"

    def get(self, request, *args, **kwargs):
        """GET the player for a venue."""
        venue = kwargs.get("venue")
        player = Player.get_player(venue)
        if player is None or not player.configured:
            return render(request, self.template_name, {"disabled": True, "venue": venue})

        return render(
            request,
            self.template_name,
            {
                "disabled": False,
                "venue": venue,
                "player": player,
                "can_request": request.user in player.get_users_with_request_permissions(),
            },
        )
