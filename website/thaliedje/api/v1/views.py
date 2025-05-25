import django_filters
import spotipy
from django.utils import timezone
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from thaliedje.api.v1.filters import PlayerFilter
from thaliedje.api.v1.pagination import StandardResultsSetPagination
from thaliedje.api.v1.serializers import (
    PlayerSerializer,
    RequestedQueueItemSerializer,
    AnonymousRequestedQueueItemSerializer,
)
from thaliedje.models import Player, SpotifyQueueItem
from thaliedje.services import request_song
from tosti.api.openapi import CustomAutoSchema


class PlayerListAPIView(ListAPIView):
    """Get an overview of all players."""

    queryset = Player.objects.all()
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = PlayerFilter
    search_fields = ["display_name"]
    serializer_class = PlayerSerializer

    def get_queryset(self):
        """Get queryset."""
        queryset = super().get_queryset().select_subclasses()
        return queryset


class PlayerRetrieveAPIView(RetrieveAPIView):
    """Get the current player."""

    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def get_queryset(self):
        """Get queryset."""
        queryset = super().get_queryset().select_subclasses()
        return queryset


class PlayerRequestsAPIView(ListAPIView):
    """Get the latest requests."""

    serializer_class = RequestedQueueItemSerializer
    queryset = SpotifyQueueItem.objects.all()
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get the queryset."""
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.queryset.filter(player=self.kwargs.get("player"), added__gte=today)

    def get_serializer_class(self):
        """Get the serializer class."""
        if self.request.user.is_authenticated:
            return RequestedQueueItemSerializer
        return AnonymousRequestedQueueItemSerializer


class PlayerQueueAPIView(APIView):
    """Get the current player's queue."""

    def get(self, request, **kwargs):
        """Get the player's current queue."""
        player = self.kwargs.get("player")
        return Response(player.queue)


class PlayerTrackSearchAPIView(APIView):
    """API view to add tracks to search for tacks."""

    schema = CustomAutoSchema(
        manual_operations=[
            {
                "name": "query",
                "in": "query",
                "required": True,
                "schema": {"type": "string"},
            },
            {
                "name": "maximum",
                "in": "query",
                "required": False,
                "schema": {"type": "int"},
            },
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
                            "artists": {
                                "type": "array",
                                "items": {"type": "string", "example": "string"},
                            },
                            "id": {
                                "type": "string",
                                "example": "6tcCTgpI1JWsgReB9ttSUD",
                            },
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

        if not player.can_request_song(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to request songs.",
            )

        query = request.GET.get("query", "")
        try:
            maximum = int(request.GET.get("maximum", 5))
        except ValueError:
            maximum = 5

        type_to_search = "track"

        if player.can_request_playlist(request.user):
            type_to_search = "album,playlist,track"

        if query != "":
            results = player.search(query, maximum, query_type=type_to_search)
        else:
            results = []
        return Response(
            status=status.HTTP_200_OK, data={"query": query, "results": results}
        )


class PlayerTrackAddAPIView(APIView):
    """API view to add tracks to the player's queue."""

    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {"id": {"type": "string", "example": "string"}},
        }
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:request"]

    def post(self, request, **kwargs):
        """Add a track to the queue."""
        player = kwargs.get("player")

        if not player.can_request_song(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to request songs.",
            )

        track_id = request.data.get("id", None)
        if track_id is None:
            raise ValidationError("A track id is required.")

        try:
            requested = request_song(player, request.user, track_id)
            player.log_action(
                request.user,
                "request_song",
                'Requested song "{}"'.format(requested.track.track_name),
            )
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)


class PlayerPlayAPIView(APIView):
    """API view to make player play."""

    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {
                "context_uri": {
                    "type": "string",
                    "example": "spotify:album:1Je1IMUlBXcx1Fz0WE7oPT",
                }
            },
        }
    )
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player play."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )

        try:
            context_uri = request.data.get("context_uri", None)
            if player.can_request_playlist(request.user) and context_uri is not None:
                player.start_playing(context_uri)
                player.log_action(
                    request.user, "play", f"Started playback {context_uri}."
                )
            else:
                player.start()
                player.log_action(request.user, "play", "Started playback.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )


class PlayerPauseAPIView(APIView):
    """API view to make player pause."""

    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player pause."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )
        try:
            player.pause()
            player.log_action(request.user, "pause", "Paused playback.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )


class PlayerVolumeAPIView(APIView):
    """API view to change the player volume."""

    serializer_class = PlayerSerializer
    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {
                "volume_percent": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "example": 75,
                }
            },
        }
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player pause."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )

        volume = int(request.data.get("volume"))
        try:
            player.volume = volume
            player.log_action(request.user, "volume", f"Changed volume to {volume}.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )


class PlayerNextAPIView(APIView):
    """API view to make player go to next song."""

    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player go to the next song."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )

        try:
            player.next()
            player.log_action(request.user, "next", "Skipped to next song.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )


class PlayerPreviousAPIView(APIView):
    """API view to make player go to previous song."""

    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def patch(self, request, **kwargs):
        """Make player go to the previous song."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )
        try:
            player.previous()
            player.log_action(request.user, "previous", "Skipped to previous song.")
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )


class PlayerShuffleAPIView(APIView):
    """API view to set shuffle state of player."""

    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {"state": {"type": "bool", "example": "true"}},
        }
    )
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player go to the previous song."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )

        state = request.data.get("state", None)
        if state is None:
            raise ValidationError("A state is required.")

        if not isinstance(state, bool):
            raise ValidationError("The state parameter should be a boolean.")

        try:
            player.shuffle = state
            player.log_action(
                request.user, "shuffle", "Set shuffle to '{}'.".format(state)
            )
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )


class PlayerRepeatAPIView(APIView):
    """API view to set repeat state of player."""

    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {"state": {"type": "string", "example": "context"}},
        }
    )
    serializer_class = PlayerSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player go to the previous song."""
        player = kwargs.get("player")
        if not player.can_control(request.user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data="You are not allowed to control this player.",
            )

        state = request.data.get("state", None)
        if state is None:
            raise ValidationError("A state is required.")

        if state != "off" and state != "context" and state != "track":
            raise ValidationError(
                "The state parameter should be one of 'off', 'context' or 'track'."
            )

        try:
            player.repeat = state
            player.log_action(
                request.user, "repeat", "Set repeat to '{}'.".format(state)
            )
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(player, context={"request": request}).data,
        )
