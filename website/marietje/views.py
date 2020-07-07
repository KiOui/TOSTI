import spotipy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template, render_to_string
from django.views.generic import TemplateView
from guardian.mixins import PermissionRequiredMixin

from marietje import services
from .models import SpotifyAccount
from .templatetags.marietje import render_queue_list, render_player

COOKIE_CLIENT_ID = "client_id"


class IndexView(TemplateView):
    """Index view for marietje."""

    template_name = "marietje/index.html"

    def get(self, request, **kwargs):
        """GET an overview of all players."""
        return render(request, self.template_name, {"players": SpotifyAccount.objects.all()})


class NowPlayingView(TemplateView):
    """Now playing view with the player for a venue."""

    template_name = "marietje/now_playing.html"

    def get(self, request, *args, **kwargs):
        """GET the player for a venue."""
        venue = kwargs.get("venue")
        player = SpotifyAccount.get_player(venue)
        if player is None or not player.configured:
            return render(request, self.template_name, {"disabled": True, "venue": venue})

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
        return get_template("marietje/player.html").render(render_player({"request": request}, player, refresh=True))

    def post(self, request, player):
        """POST request for refreshing the player."""
        return JsonResponse({"data": self.render_template(player, request)})


class QueueRefreshView(LoginRequiredMixin, TemplateView):
    """Refresh the queue."""

    def post(self, request, player):
        """POST request for refreshing the queue."""
        queue = get_template("marietje/queue.html").render(render_queue_list(player, refresh=True))
        return JsonResponse({"data": queue})


class SearchView(PermissionRequiredMixin, TemplateView):
    """Search track view."""

    permission_required = "marietje.can_request"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for SearchView.

        Search a Spotify track.
        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the search page with the response to the search query
        """
        player = kwargs.get("player")
        query = request.POST.get("query", None)
        request_id = request.POST.get("id", "")
        try:
            maximum = int(request.POST.get("maximum", 5))
        except ValueError:
            maximum = 5

        if query is not None:
            results = services.search_tracks(query, player, maximum)
            rendered_results = render_to_string("marietje/search.html", {"refresh": True, "tracks": results})
            return JsonResponse({"query": query, "id": request_id, "result": rendered_results})
        else:
            return JsonResponse({"query": "", "id": request_id, "result": ""})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("player")


class AddView(PermissionRequiredMixin, TemplateView):
    """Add a track to the queue view."""

    permission_required = "marietje.can_request"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for AddView.

        Add a track to the Spotify queue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response indicating the track has been added to the queue or an error
        """
        player = kwargs.get("player")
        track_id = request.POST.get("id", None)
        if track_id is not None:
            try:
                services.request_song(request.user, player, track_id)
            except spotipy.SpotifyException:
                return JsonResponse({"error": True, "msg": "The track could not be added to the queue"})
            return JsonResponse({"error": False, "msg": "Track added to queue"})
        else:
            return JsonResponse({"error": True, "msg": "No track ID specified"})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("player")


class PlayView(PermissionRequiredMixin, TemplateView):
    """Start playback view."""

    permission_required = "marietje.can_control"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for PlayView.

        Start playback on a Spotify queue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response indicating playback has started or an error
        """
        player = kwargs.get("player")
        try:
            services.player_start(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to start playback, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("player")


class PauseView(PermissionRequiredMixin, TemplateView):
    """Pause playback view."""

    permission_required = "marietje.can_control"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for PauseView.

        Pause playback on a Spotify queue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response indicating playback has paused or an error
        """
        player = kwargs.get("player")
        try:
            services.player_pause(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to pause playback, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("player")


class NextView(PermissionRequiredMixin, TemplateView):
    """Next track view."""

    permission_required = "marietje.can_control"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for NextView.

        Go to the next track in a Spotify queue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response indicating the track has been skipped or an error
        """
        player = kwargs.get("player")
        try:
            services.player_next(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to skip track, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("player")


class PreviousView(PermissionRequiredMixin, TemplateView):
    """Previous track view."""

    permission_required = "marietje.can_control"
    return_403 = True
    accept_global_perms = True

    def post(self, request, **kwargs):
        """
        POST request for NextView.

        Go to the previous track in a Spotify queue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a json response indicating the track has been reverted or an error
        """
        player = kwargs.get("player")
        try:
            services.player_previous(player)
        except spotipy.SpotifyException:
            return JsonResponse(
                {"error": True, "msg": "Failed to rewind track, is the registered Spotify device online?"}
            )
        return JsonResponse({"error": False})

    def get_object(self):
        """Get the object for this view."""
        return self.kwargs.get("player")
