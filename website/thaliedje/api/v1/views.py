import django_filters
import spotipy
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from thaliedje import services
from thaliedje.api.v1.filters import PlayerFilter
from thaliedje.api.v1.pagination import StandardResultsSetPagination
from thaliedje.api.v1.serializers import PlayerSerializer, QueueItemSerializer
from thaliedje.models import Player, SpotifyQueueItem
from thaliedje.services import user_is_blacklisted
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
        return self.queryset.filter(player=self.kwargs.get("player"))


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
        if user_is_blacklisted(self.request.user):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are blacklisted.")

        player = kwargs.get("player")
        query = request.GET.get("query", "")
        try:
            maximum = int(request.GET.get("maximum", 5))
        except ValueError:
            maximum = 5

        if query != "":
            results = services.search_tracks(query, player, maximum)
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
        if user_is_blacklisted(self.request.user):
            return Response(status=status.HTTP_403_FORBIDDEN, data="You are blacklisted.")

        player = kwargs.get("player")
        track_id = request.data.get("id", None)
        if track_id is None:
            raise ValidationError("A track id is required.")

        try:
            services.request_song(request.user, player, track_id)
        except spotipy.SpotifyException:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(status=status.HTTP_200_OK)


class PlayerPlayAPIView(APIView):
    """API view to make player play."""

    serializer_class = PlayerSerializer
    permission_required = "thaliedje.can_control"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player play."""
        player = kwargs.get("player")
        try:
            services.player_start(player)
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
    permission_required = "thaliedje.can_control"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player pause."""
        player = kwargs.get("player")
        try:
            services.player_pause(player)
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
    permission_required = "thaliedje.can_control"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player pause."""
        player = kwargs.get("player")
        volume = int(request.data.get("volume"))
        try:
            services.set_player_volume(player, volume)
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
    permission_required = "thaliedje.can_control"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player go to the next song."""
        player = kwargs.get("player")
        try:
            services.player_next(player)
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
    permission_required = "thaliedje.can_control"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["thaliedje:manage"]

    def get_permission_object(self):
        """Get the player to check permissions for."""
        return self.kwargs.get("player")

    def patch(self, request, **kwargs):
        """Make player go to the previous song."""
        player = kwargs.get("player")
        try:
            services.player_previous(player)
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(player, context={"request": request}).data
        )
