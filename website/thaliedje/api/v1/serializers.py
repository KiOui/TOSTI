from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from thaliedje import models
from thaliedje.models import Player
from users.api.v1.serializers import UserSerializer


class TrackSerializer(serializers.ModelSerializer):
    """Track serializer."""

    track_artists = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_track_artists(self, instance):
        """Get artist names instead of ID."""
        return [x.artist_name for x in instance.track_artists.all()]

    class Meta:
        """Meta class."""

        model = models.SpotifyTrack
        fields = ["track_id", "track_name", "track_artists"]


class AnonymousRequestedQueueItemSerializer(serializers.ModelSerializer):
    """Requested Queue Item Serializer."""

    track = TrackSerializer(many=False, read_only=True)

    class Meta:
        """Meta class."""

        model = models.SpotifyQueueItem
        fields = [
            "track",
            "added",
        ]


class RequestedQueueItemSerializer(serializers.ModelSerializer):
    """Requested Queue Item Serializer."""

    track = TrackSerializer(many=False, read_only=True)
    requested_by = UserSerializer(many=False)

    class Meta:
        """Meta class."""

        model = models.SpotifyQueueItem
        fields = [
            "track",
            "added",
            "requested_by",
        ]


class _TrackInfoSerializer(serializers.Serializer):
    """Inline schema for the ``track`` field emitted by ``PlayerSerializer``."""

    image = serializers.CharField(allow_null=True)
    name = serializers.CharField(allow_null=True)
    artists = serializers.ListField(child=serializers.CharField())


class PlayerSerializer(serializers.ModelSerializer):
    """Player serializer."""

    track = serializers.SerializerMethodField()
    is_playing = serializers.BooleanField(read_only=True)
    shuffle = serializers.BooleanField(read_only=True, allow_null=True)
    repeat = serializers.CharField(read_only=True, allow_null=True)
    current_volume = serializers.FloatField(source="volume", allow_null=True)
    timestamp = serializers.IntegerField(source="current_timestamp", allow_null=True)
    progress_ms = serializers.IntegerField(
        source="current_progress_ms", allow_null=True
    )
    duration_ms = serializers.IntegerField(
        source="current_track_duration_ms", allow_null=True
    )

    @extend_schema_field(_TrackInfoSerializer)
    def get_track(self, instance):
        """Get track as a dict."""
        return {
            "image": instance.current_image,
            "name": instance.current_track_name,
            "artists": instance.current_artists,
        }

    class Meta:
        """Meta class."""

        model = Player
        fields = [
            "id",
            "slug",
            "display_name",
            "venue",
            "track",
            "is_playing",
            "shuffle",
            "repeat",
            "current_volume",
            "timestamp",
            "progress_ms",
            "duration_ms",
        ]
