import spotipy
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from marietje import services
from marietje.api.v1.pagination import StandardResultsSetPagination
from marietje.api.v1.serializers import PlayerSerializer, QueueItemSerializer
from marietje.models import Player, SpotifyQueueItem


class PlayerListAPIView(ListAPIView):
    """
    Player List API View.

    Permissions required: None

    Use this endpoint to get a list of all installed Spotify Players.
    """

    serializer_class = PlayerSerializer
    queryset = Player.objects.all()


class PlayerRetrieveAPIView(RetrieveAPIView):
    """
    Player Retrieve API View.

    Permissions required: None

    Use this endpoint to get the details of an installed Spotify Players.
    """

    serializer_class = PlayerSerializer
    queryset = Player.objects.all()


class PlayerQueueListAPIView(ListAPIView):
    """
    Player Queue List API View.

    Permissions required: None

    Use this endpoint to get a list of tracks that are in the queue of the Spotify Player. Tracks are sorted on the time
    that they were added, the track that was added last will appear first in the list.
    """

    serializer_class = QueueItemSerializer
    queryset = SpotifyQueueItem.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(player=self.kwargs.get("player"))


@api_view(["GET"])
def track_search(request, **kwargs):
    """
    Track Search API View.

    Permissions required: marietje.can_request

    Search for a Spotify track.

    This method requires a query GET parameter to be present indicating the query to search for. Optionally an id GET
    parameter may be specified which will be echoed in the response.
    """
    player = kwargs.get("player")
    query = request.GET.get("query", "")
    request_id = request.GET.get("id", None)
    try:
        maximum = int(request.GET.get("maximum", 5))
    except ValueError:
        maximum = 5
    if request.user.has_perm("marietje.can_request", player):
        if query != "":
            results = services.search_tracks(query, player, maximum)
        else:
            results = []
        return Response(status=status.HTTP_200_OK, data={"query": query, "id": request_id, "results": results})
    else:
        raise PermissionDenied


@api_view(["POST"])
def track_add(request, **kwargs):
    """
    Track Add API View.

    Permission required: marietje.can_request

    This method requires an ID POST parameter to be present indicating the Spotify ID of the track that must be added
    to the queue.
    """
    player = kwargs.get("player")
    track_id = request.POST.get("id", None)
    if request.user.has_perm("marietje.can_request", player):
        if track_id is not None:
            try:
                services.request_song(request.user, player, track_id)
            except spotipy.SpotifyException:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response(status=status.HTTP_200_OK)
        else:
            raise ValidationError("A track id is required.")
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def player_play(request, **kwargs):
    """
    Player Play API View.

    Permission required: marietje.can_request

    Start playback on a Player.
    """
    player = kwargs.get("player")
    if request.user.has_perm("marietje.can_request", player):
        try:
            services.player_start(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def player_pause(request, **kwargs):
    """
    Player Pause API View.

    Permission required: marietje.can_request

    Pause playback on a Player.
    """
    player = kwargs.get("player")
    if request.user.has_perm("marietje.can_request", player):
        try:
            services.player_pause(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def player_next(request, **kwargs):
    """
    Player Next API View.

    Permission required: marietje.can_request

    Skip the current song of a Player.
    """
    player = kwargs.get("player")
    if request.user.has_perm("marietje.can_request", player):
        try:
            services.player_next(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def player_previous(request, **kwargs):
    """
    Player Previous API View.

    Permission required: marietje.can_request

    Go back to the previous song of a Player.
    """
    player = kwargs.get("player")
    if request.user.has_perm("marietje.can_request", player):
        try:
            services.player_previous(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)
    else:
        raise PermissionDenied
