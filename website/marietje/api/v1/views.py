import spotipy
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from marietje import services
from marietje.api.v1.pagination import StandardResultsSetPagination
from marietje.api.v1.serializers import PlayerSerializer, QueueItemSerializer
from marietje.models import Player, SpotifyQueueItem
from tosti.api.permissions import HasPermissionOnObject
from tosti.api.openapi import CustomAutoSchema


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

    Use this endpoint to get a list of tracks that are in the queue of the Spotify Player. Tracks are sorted on the
    time that they were added, the track that was added last will appear first in the list.
    """

    serializer_class = QueueItemSerializer
    queryset = SpotifyQueueItem.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(player=self.kwargs.get("player"))


class PlayerTrackSearchAPIView(APIView):
    """Player Track Search API View."""

    schema = CustomAutoSchema(
        manual_operations=[{"name": "query", "in": "query", "required": True, "schema": {"type": "string"}}],
        response_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "example": "string"},
                "id": {"type": "int", "example": "123"},
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "example": "string"},
                            "artists": {"type": "array", "items": {"type": "string", "example": "string"}},
                            "id": {"type": "string", "example": "string"},
                        },
                    },
                },
            },
        },
    )
    permission_required = "marietje.can_request"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        return self.kwargs.get("player")

    def get(self, request, **kwargs):
        """
        Search for a Spotify track.

        Permission required: marietje.can_request

        Use this endpoint to search for a Spotify Track. Tracks can be searched via their Spotify id.
        """
        player = kwargs.get("player")
        query = request.GET.get("query", "")
        request_id = request.GET.get("id", None)
        try:
            maximum = int(request.GET.get("maximum", 5))
        except ValueError:
            maximum = 5

        if query != "":
            results = services.search_tracks(query, player, maximum)
        else:
            results = []
        return Response(status=status.HTTP_200_OK, data={"query": query, "id": request_id, "results": results})


class PlayerTrackAddAPIView(APIView):
    """Player Track Add API View."""

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"id": {"type": "string", "example": "string"}}}
    )
    permission_required = "marietje.can_request"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        return self.kwargs.get("player")

    def post(self, request, **kwargs):
        """
        Add a Spotify Track to the queue.

        Permission required: marietje.can_request

        Use this endpoint to add a spotify track to the queue.
        """
        player = kwargs.get("player")
        track_id = request.POST.get("id", None)
        if track_id is not None:
            try:
                services.request_song(request.user, player, track_id)
            except spotipy.SpotifyException:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response(status=status.HTTP_200_OK)
        else:
            raise ValidationError("A track id is required.")


class PlayerPlayAPIView(APIView):
    """Player Play API View."""

    permission_required = "marietje.can_control"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """
        Player Play API View.

        Permission required: marietje.can_control

        Start playback on a Player.
        """
        player = kwargs.get("player")
        try:
            services.player_start(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)


class PlayerPauseAPIView(APIView):
    """Player Pause API View."""

    permission_required = "marietje.can_control"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """
        Player Pause API View.

        Permission required: marietje.can_control

        Start playback on a Player.
        """
        player = kwargs.get("player")
        try:
            services.player_pause(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)


class PlayerNextAPIView(APIView):
    """Player Next API View."""

    permission_required = "marietje.can_control"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """
        Player Play API View.

        Permission required: marietje.can_control

        Start playback on a Player.
        """
        player = kwargs.get("player")
        try:
            services.player_next(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)


class PlayerPreviousAPIView(APIView):
    """Player Previous API View."""

    permission_required = "marietje.can_control"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """
        Player Previous API View.

        Permission required: marietje.can_control

        Start playback on a Player.
        """
        player = kwargs.get("player")
        try:
            services.player_previous(player)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)
