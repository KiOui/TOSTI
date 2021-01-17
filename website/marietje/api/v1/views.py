import spotipy
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from marietje import services
from marietje.api.v1.pagination import StandardResultsSetPagination
from marietje.api.v1.serializers import PlayerSerializer, PlayerRetrieveSerializer, QueueItemSerializer
from marietje.models import Player, SpotifyQueueItem


class PlayerListAPIView(ListAPIView):
    """Player List API View."""

    serializer_class = PlayerSerializer
    queryset = Player.objects.all()


class PlayerRetrieveAPIView(RetrieveAPIView):
    """Player Retrieve API View."""

    serializer_class = PlayerRetrieveSerializer
    queryset = Player.objects.all()


class PlayerQueueListAPIView(ListAPIView):
    """Player Queue List API View."""

    serializer_class = QueueItemSerializer
    queryset = SpotifyQueueItem.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(player=self.kwargs.get("player"))


@api_view(["GET"])
def track_search(request, **kwargs):
    """
    Search for Spotify tracks.

    This method requires a query GET parameter to be present indicating the query to search for. Optionally an id GET
    parameter may be specified which will be echoed in the response.
    :param request: the request
    :param kwargs: keyword arguments
    :return: A PermissionDenied error on permission denied or a 200 response with the results
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
    Add a track to the queue of a Player.

    The Spotify ID of a track must be present as the id POST parameter.
    :param request: the request
    :param kwargs: keyword arguments
    :return: A PermissionDenied error on permission denied, A validation error when no track id is specified, a 503
    response when a Spotify Exception occurs or a 200 response on success
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
    Play a Player.

    :param request: the request
    :param kwargs: keyword arguments
    :return: A PermissionDenied error on permission denied, a 503 response when a Spotify Exception occurs or a 200
    response on success
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
    Pause a Player.

    :param request: the request
    :param kwargs: keyword arguments
    :return: A PermissionDenied error on permission denied, a 503 response when a Spotify Exception occurs or a 200
    response on success
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
    Skip a song of a Player.

    :param request: the request
    :param kwargs: keyword arguments
    :return: A PermissionDenied error on permission denied, a 503 response when a Spotify Exception occurs or a 200
    response on success
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
    Go back a song of a Player.

    :param request: the request
    :param kwargs: keyword arguments
    :return: A PermissionDenied error on permission denied, a 503 response when a Spotify Exception occurs or a 200
    response on success
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
