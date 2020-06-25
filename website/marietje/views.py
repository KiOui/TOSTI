import logging

import spotipy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.template.loader import get_template, render_to_string
from django.views.generic import TemplateView

from .models import SpotifyAccount, SpotifyQueueItem
from .services import create_track_database_information
from .templatetags.queue import render_queue_list, render_player
from django.contrib.admin.views.decorators import staff_member_required

COOKIE_CLIENT_ID = "client_id"


class IndexView(TemplateView):
    """Index view for marietje."""

    template_name = "marietje/index.html"

    def get(self, request, **kwargs):
        """
        GET request for IndexView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the index page
        """
        return render(
            request, self.template_name, {"players": SpotifyAccount.objects.all()}
        )


class NowPlayingView(LoginRequiredMixin, TemplateView):
    """Now playing view."""

    template_name = "marietje/now_playing.html"

    def get(self, request, **kwargs):
        """
        GET request for NowPlayingView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the now playing page
        """
        venue = kwargs.get("venue")
        player = SpotifyAccount.get_player(venue)
        if player is None or not player.configured:
            return render(
                request, self.template_name, {"disabled": True, "venue": venue}
            )

        return render(
            request,
            self.template_name,
            {"disabled": False, "venue": venue, "spotify": player},
        )


class PlayerRefreshView(LoginRequiredMixin, TemplateView):
    """Refresh the player."""

    @staticmethod
    def render_template(spotify, request):
        """
        Render the player template.

        :param venue: a Venue object
        :param request: the request
        :param controls: whether or not to display the controls
        :return: a render of the player.html template
        """
        return get_template("marietje/player.html").render(
            render_player({"request": request}, spotify, refresh=True)
        )

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
        spotify = kwargs.get("spotify")
        return JsonResponse({"data": self.render_template(spotify, request)})


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
        spotify = kwargs.get("spotify")
        queue = get_template("marietje/queue.html").render(
            render_queue_list(spotify, refresh=True)
        )
        return JsonResponse({"data": queue})


@login_required
def search_view(request, **kwargs):
    """
    Call the Spotify API to search for a track.

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
            spotify = kwargs.get("spotify")
            result = spotify.spotify.search(query, limit=maximum, type="track")
            result = sorted(result["tracks"]["items"], key=lambda x: -x["popularity"])
            trimmed_result = [
                {
                    "name": x["name"],
                    "artists": [y["name"] for y in x["artists"]],
                    "id": x["id"],
                }
                for x in result
            ]
            rendered_results = render_to_string(
                "marietje/search.html", {"refresh": True, "tracks": trimmed_result}
            )
            return JsonResponse(
                {"query": query, "id": request_id, "result": rendered_results}
            )
        else:
            return JsonResponse({"query": "", "id": request_id, "result": ""})
    else:
        return Http404("This view can only be called with a POST request.")


@login_required
def add_view(request, **kwargs):
    """
    Call the Spotify API to add a track to the queue.

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
            spotify = kwargs.get("spotify")
            try:
                track_info = spotify.spotify.track(track_id)
                track = create_track_database_information(track_info)
                SpotifyQueueItem.objects.create(
                    track=track,
                    spotify_settings_object=spotify,
                    requested_by=request.user,
                )
                spotify.spotify.add_to_queue(
                    track_id, device_id=spotify.playback_device_id
                )
            except spotipy.exceptions.SpotifyException as e:
                logging.error(e)
                return JsonResponse(
                    {"error": True, "msg": "The track could not be added to the queue"}
                )
            return JsonResponse({"error": False, "msg": "Track added to queue"})
        else:
            return JsonResponse({"error": True, "msg": "No track ID specified"})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def play_view(request, **kwargs):
    """
    Call the Spotify API for starting the playback.

    :param request: the request
    :param kwargs: keyword arguments
    :return: nothing
    """
    if request.method == "POST":
        spotify = kwargs.get("spotify")
        try:
            spotify.spotify.start_playback(device_id=spotify.playback_device_id)
        except spotipy.exceptions.SpotifyException as e:
            logging.error(e)
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to start playback, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def pause_view(request, **kwargs):
    """
    Call the Spotify API for pausing the playback.

    :param request: the request
    :param kwargs: keyword arguments
    :return: nothing
    """
    if request.method == "POST":
        spotify = kwargs.get("spotify")
        try:
            spotify.spotify.pause_playback(spotify.playback_device_id)
        except spotipy.exceptions.SpotifyException as e:
            logging.error(e)
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to pause playback, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def next_view(request, **kwargs):
    """
    Call the Spotify API for the next track.

    :param request: the request
    :param kwargs: keyword arguments
    :return: nothing
    """
    if request.method == "POST":
        spotify = kwargs.get("spotify")
        try:
            spotify.spotify.next_track()
        except spotipy.exceptions.SpotifyException as e:
            logging.error(e)
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to skip track, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")


@staff_member_required
def previous_view(request, **kwargs):
    """
    Call the Spotify API for the previous track.

    :param request: the request
    :param kwargs: keyword arguments
    :return: nothing
    """
    if request.method == "POST":
        spotify = kwargs.get("spotify")
        try:
            spotify.spotify.previous_track()
        except spotipy.exceptions.SpotifyException as e:
            logging.error(e)
            return JsonResponse(
                {
                    "error": True,
                    "msg": "Failed to rewind track, is the registered Spotify device online?",
                }
            )
        return JsonResponse({"error": False})
    else:
        return Http404("This view can only be called with a POST request.")
