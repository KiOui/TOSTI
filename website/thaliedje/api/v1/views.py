import django_filters
import spotipy
from django.utils import timezone
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from thaliedje import services
from thaliedje.api.v1.filters import PlayerFilter
from thaliedje.api.v1.pagination import StandardResultsSetPagination
from thaliedje.api.v1.serializers import PlayerSerializer, QueueItemSerializer, AnonymousQueueItemSerializer
from thaliedje.models import Player, SpotifyQueueItem
from thaliedje.services import can_request_song, can_request_playlist, can_control_player, log_player_action
from tosti.api.openapi import CustomAutoSchema
from tosti.api.permissions import HasPermissionOnObject


class PlayerListAPIView(ListAPIView):
    """Get an overview of all players."""

    serializer_class = PlayerSerializer
    queryset = Player.objects.all()
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = PlayerFilter
    search_fields = ["display_name"]


class PlayerRetrieveAPIView(RetrieveAPIView):
    """Get the current player."""

    serializer_class = PlayerSerializer
    queryset = Player.objects.all()


class PlayerQueueListAPIView(ListAPIView):
    """Get the current player's queue."""

    serializer_class = QueueItemSerializer
    queryset = SpotifyQueueItem.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get the queryset."""
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.queryset.filter(player=self.kwargs.get("player"), added__gte=today)

    def get_serializer_class(self):
        """Get the serializer class."""
        if self.request.user.is_authenticated:
            return QueueItemSerializer
        return AnonymousQueueItemSerializer


class PlayerTrackSearchAPIView(APIView):
    """API view to add tracks to search for tacks."""

    schema = CustomAutoSchema(
        manual_operations=[
            {"name": "query", "in": "query", "required": True, "schema": {"type": "string"}},
            {"name": "maximum", "in": "query", "required": False, "schema": {"type": "int"}},
        ],
        response_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "example": "string"},
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "example": "string"},
                            "artists": {"type": "array", "items": {"type": "string", "example": "string"}},
                            "id": {"type": "string", "example": "6tcCTgpI1JWsgReB9ttSUD"},
                        },
                    },
                },
            },
        },
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:request"]

    def get(self, request, **kwargs):
        """Search for a track."""
        player = kwargs.get("player")

        if not can_request_song(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to request songs.")

        query = request.GET.get("query", "")
        try:
            maximum = int(request.GET.get("maximum", 5))
        except ValueError:
            maximum = 5

        type_to_search = "track"

        if can_request_playlist(request.user, player):
            type_to_search = "album,playlist,track"

        if query != "":
            results = services.search_tracks(query, player, maximum, type=type_to_search)
        else:
            results = []
        return Response(status=status.HTTP_200_OK, data={"query": query, "results": results})


class PlayerTrackAddAPIView(APIView):
    """API view to add tracks to the player's queue."""

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"id": {"type": "string", "example": "string"}}}
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:request"]

    def post(self, request, **kwargs):
        """Add a track to the queue."""
        player = kwargs.get("player")

        if not can_request_song(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to request songs.")

        track_id = request.data.get("id", None)
        if track_id is None:
            raise ValidationError("A track id is required.")

        try:
            services.request_song(request.user, player, track_id)
            log_player_action(request.user, player, "request_song", 'Requested song "{}"'.format(track_id))
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)


class PlayerPlayAPIView(APIView):
    """API view to make player play."""

    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {"context_uri": {"type": "string", "example": "spotify:album:1Je1IMUlBXcx1Fz0WE7oPT"}},
        }
    )
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player play."""
        player = kwargs.get("player")
        if not can_control_player(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to control this player.")

        try:
            context_uri = request.data.get("context_uri", None)
            if can_request_playlist(request.user, player) and context_uri is not None:
                services.player_start(player, context_uri=context_uri)
            else:
                services.player_start(player)
            log_player_action(request.user, player, "play", "Started playback.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(player, context={"request": request}).data
        )


class PlayerPauseAPIView(APIView):
    """API view to make player pause."""

    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player pause."""
        player = kwargs.get("player")
        if not can_control_player(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to control this player.")
        try:
            services.player_pause(player)
            log_player_action(request.user, player, "pause", "Paused playback.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(player, context={"request": request}).data
        )


class PlayerVolumeAPIView(APIView):
    """API view to change the player volume."""

    serializer_class = PlayerSerializer
    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {"volume_percent": {"type": "integer", "minimum": 0, "maximum": 100, "example": 75}},
        }
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player pause."""
        player = kwargs.get("player")
        if not can_control_player(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to control this player.")

        volume = int(request.data.get("volume"))
        try:
            services.set_player_volume(player, volume)
            log_player_action(request.user, player, "volume", f"Changed volume to {volume}.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(player, context={"request": request}).data
        )


class PlayerNextAPIView(APIView):
    """API view to make player go to next song."""

    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player go to the next song."""
        player = kwargs.get("player")
        if not can_control_player(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to control this player.")

        try:
            services.player_next(player)
            log_player_action(request.user, player, "next", "Skipped to next song.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(player, context={"request": request}).data
        )


class PlayerPreviousAPIView(APIView):
    """API view to make player go to previous song."""

    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player go to the previous song."""
        player = kwargs.get("player")
        if not can_control_player(request.user, player):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are not allowed to control this player.")
        try:
            services.player_previous(player)
            log_player_action(request.user, player, "previous", "Skipped to previous song.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(player, context={"request": request}).data
        )
