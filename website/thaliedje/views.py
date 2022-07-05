from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from .models import SpotifyQueueItem
from .services import user_is_blacklisted


class IndexView(TemplateView):
    """Index view for thaliedje."""

    template_name = "thaliedje/index.html"


class NowPlayingView(TemplateView):
    """Now playing view with the player for a venue."""

    template_name = "thaliedje/now_playing.html"

    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        player = kwargs.get("player")
        context["player"] = player

        if not player.configured:
            context["disabled"] = True
            return context

        context["venue"] = player.venue

        context["can_request"] = self.request.user.is_authenticated and not user_is_blacklisted(self.request.user)
        return context


def render_account_history_tab(request, item, current_page_url):
    """Render the account history tab on the user page."""
    song_requests = SpotifyQueueItem.objects.filter(requested_by=request.user).order_by("-added")
    page = request.GET.get("page", 1) if (item["slug"] == request.GET.get("active", False)) else 1
    paginator = Paginator(song_requests, per_page=50)
    return render_to_string(
        "thaliedje/account_history.html",
        context={"page_obj": paginator.get_page(page), "current_page_url": current_page_url, "item": item},
    )
