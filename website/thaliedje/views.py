from django.core.paginator import Paginator
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from .models import Player, SpotifyQueueItem
from .services import user_is_blacklisted

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
                "can_request": not user_is_blacklisted(request.user),
            },
        )


def render_account_history_tab(request, item, current_page_url):
    """Render the account history tab on the user page."""
    song_requests = SpotifyQueueItem.objects.filter(requested_by=request.user).order_by("-added")
    page = request.GET.get("page", 1) if (item["slug"] == request.GET.get("active", False)) else 1
    paginator = Paginator(song_requests, per_page=50)
    return render_to_string(
        "thaliedje/account_history.html",
        context={"page_obj": paginator.get_page(page), "current_page_url": current_page_url, "item": item},
    )
