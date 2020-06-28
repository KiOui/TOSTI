import spotipy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.template.loader import get_template, render_to_string
from django.views.generic import TemplateView
from guardian.decorators import permission_required_or_403

from marietje import services
from .models import SpotifyAccount
from .templatetags.marietje import render_queue_list, render_player

COOKIE_CLIENT_ID = "client_id"


class IndexView(TemplateView):
    """Index view for marietje."""

    template_name = "marietje/index.html"

    def get(self, request, **kwargs):
        """GET an overview of all players."""
        return render(
            request, self.template_name, {"players": SpotifyAccount.objects.all()}
        )


class NowPlayingView(TemplateView):
    """Now playing view with the player for a venue."""

    template_name = "marietje/now_playing.html"

    def get(self, request, venue):
        """GET the player for a venue."""
        player = SpotifyAccount.get_player(venue)
        if player is None or not player.configured:
            return render(
                request, self.template_name, {"disabled": True, "venue": venue}
            )

        return render(
            request,
            self.template_name,
            {
                "disabled": False,
                "venue": venue,
                "player": player,
                "can_request": request.user.has_perm("marietje.can_request", player),
            },
        )


class PlayerRefreshView(TemplateView):
    """Refresh the player."""

    @staticmethod
    def render_template(player, request):
        """Render the player template."""
        return get_template("marietje/player.html").render(
            render_player({"request": request}, player, refresh=True)
        )

    def post(self, request, player):
        """POST request for refreshing the player."""
        return JsonResponse({"data": self.render_template(player, request)})


class QueueRefreshView(LoginRequiredMixin, TemplateView):
    """Refresh the queue."""

    def post(self, request, player):
        """POST request for refreshing the queue."""
        queue = get_template("marietje/queue.html").render(
            render_queue_list(player, refresh=True)
        )
        return JsonResponse({"data": queue})


@permission_required_or_403(
    "marietje.can_request", (SpotifyAccount, "display_name", "player")
)
def search_view(request, player):
    """
    Search for a track on Spotify.

    :param request: the request
    :param player: the SpotiftAccount player
    :return: a JsonResponse object of the following form:
    {
        query: [queried string],
        id: [request id],
        result: [rendered result HTML element]
    }
    """
    if request.method == "POST":
        query = request.POST.get("query", None)
        request_id = request.POST.get("id", "")
        try:
            maximum = int(request.POST.get("maximum", 5))
        except ValueError:
            maximum = 5

        if query is not None:
            results = services.search_tracks(query, player, maximum)
            rendered_results = render_to_string(
                "marietje/search.html", {"refresh": True, "tracks": results}
            )
            return JsonResponse(
                {"query": query, "id": request_id, "result": rendered_results}
            )
        else:
            return JsonResponse({"query": "", "id": request_id, "result": ""})
    else:
        return Http404("This view can only be called with a POST request.")


@permission_required_or_403(
    "marietje.can_request", (SpotifyAccount, "display_name", "player")
)
def add_view(request, player):
    """
    Add a Spotify track to the queue of a player.

    :param request: the request
    :param player: the SpotiftAccount player
    :return: a JsonResponse object of the following form
    {
        error: [True|False],
        msg: [Message]
    }
    """
    if request.method == "POST":
        track_id = request.POST.get("id", None)
        if track_id is not None:
            try:
                services.request_song(request.user, player, track_id)
            except spotipy.SpotifyException:
                return JsonResponse(
                    {"error": True, "msg": "The track could not be added to the queue"}
                )
            return JsonResponse({"error": False, "msg": "Track added to queue"})
        else:
            return JsonResponse({"error": True, "msg": "No track ID specified"})
    else:
        return Http404("This view can only be called with a POST request.")


@permission_required_or_403(
    "marietje.can_control", (SpotifyAccount, "display_name", "player")
)
def play_view(request, player):
    """Start playing the player."""
    if request.method == "POST":
        try:
            services.player_start(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to start playback, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@permission_required_or_403(
    "marietje.can_control", (SpotifyAccount, "display_name", "player")
)
def pause_view(request, player):
    """Pause the player."""
    if request.method == "POST":
        try:
            services.player_pause(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to pause playback, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@permission_required_or_403(
    "marietje.can_control", (SpotifyAccount, "display_name", "player")
)
def next_view(request, player):
    """Skip the player to the next track."""
    if request.method == "POST":
        try:
            services.player_next(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to skip track, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@permission_required_or_403(
    "marietje.can_control", (SpotifyAccount, "display_name", "player")
)
def previous_view(request, player):
    """Go back to the previous track on a player."""
    if request.method == "POST":
        try:
            services.player_previous(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to rewind track, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")
