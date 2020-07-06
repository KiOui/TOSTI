import spotipy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.template.loader import get_template, render_to_string
from django.views.generic import TemplateView

from marietje import services
from .models import SpotifyAccount
from .templatetags.marietje import render_queue_list, render_player
from django.contrib.admin.views.decorators import staff_member_required

COOKIE_CLIENT_ID = "client_id"


class IndexView(TemplateView):
    """Index view for marietje."""

    template_name = "marietje/index.html"

    def get(self, request, **kwargs):
        """GET an overview of all players."""
        return render(request, self.template_name, {"players": SpotifyAccount.objects.all()})


class NowPlayingView(LoginRequiredMixin, TemplateView):
    """Now playing view with the player for a venue."""

    template_name = "marietje/now_playing.html"

    def get(self, request, **kwargs):
        """GET the player for a venue."""
        venue = kwargs.get("venue")
        player = SpotifyAccount.get_player(venue)
        if player is None or not player.configured:
            return render(request, self.template_name, {"disabled": True, "venue": venue})

        return render(request, self.template_name, {"disabled": False, "venue": venue, "player": player},)


class PlayerRefreshView(LoginRequiredMixin, TemplateView):
    """Refresh the player."""

    @staticmethod
    def render_template(player, request):
        """Render the player template."""
        return get_template("marietje/player.html").render(render_player({"request": request}, player, refresh=True))

    def post(self, request, **kwargs):
        """
        POST request for refreshing the player.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The player in the following JSON format:
        {
            data: [player]
        }
        """
        player = kwargs.get("player")
        return JsonResponse({"data": self.render_template(player, request)})


class QueueRefreshView(LoginRequiredMixin, TemplateView):
    """Refresh the queue."""

    def post(self, request, **kwargs):
        """
        POST request for refreshing the queue.

        :param request: the request
        :param kwargs: keyword arguments
        :return: The player in the following JSON format:
        {
            data: [queue]
        }
        """
        player = kwargs.get("player")
        queue = get_template("marietje/queue.html").render(render_queue_list(player, refresh=True))
        return JsonResponse({"data": queue})


@login_required
def search_view(request, **kwargs):
    """
    Search for a track on Spotify.

    :param request: the request
    :param kwargs: keyword arguments
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
            player = kwargs.get("player")
            results = services.search_tracks(query, player, maximum)
            rendered_results = render_to_string("marietje/search.html", {"refresh": True, "tracks": results})
            return JsonResponse({"query": query, "id": request_id, "result": rendered_results})
        else:
            return JsonResponse({"query": "", "id": request_id, "result": ""})
    else:
        return Http404("This view can only be called with a POST request.")


@login_required
def add_view(request, **kwargs):
    """
    Add a Spotify track to the queue of a player.

    :param request: the request
    :param kwargs: keyword arguments
    :return: a JsonResponse object of the following form
    {
        error: [True|False],
        msg: [Message]
    }
    """
    if request.method == "POST":
        track_id = request.POST.get("id", None)
        if track_id is not None:
            player = kwargs.get("player")
            try:
                services.request_song(request.user, player, track_id)
            except spotipy.SpotifyException:
                return JsonResponse({"error": True, "msg": "The track could not be added to the queue"})
            return JsonResponse({"error": False, "msg": "Track added to queue"})
        else:
            return JsonResponse({"error": True, "msg": "No track ID specified"})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def play_view(request, **kwargs):
    """Start playing the player."""
    if request.method == "POST":
        try:
            services.player_start(kwargs.get("player"))
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to start playback, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def pause_view(request, **kwargs):
    """Pause the player."""
    if request.method == "POST":
        try:
            services.player_pause(kwargs.get("player"))
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to pause playback, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def next_view(request, **kwargs):
    """Skip the player to the next track."""
    if request.method == "POST":
        try:
            services.player_next(kwargs.get("player"))
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to skip track, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def previous_view(request, **kwargs):
    """Go back to the previous track on a player."""
    if request.method == "POST":
        try:
            services.player_previous(kwargs.get("player"))
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to rewind track, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")
