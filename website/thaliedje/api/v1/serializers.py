from thaliedje.models import Player
from users.api.v1.serializers import UserSerializer
from rest_framework import serializers
from thaliedje import models


class TrackSerializer(serializers.ModelSerializer):
    """Track serializer."""

    track_artists = serializers.SerializerMethodField()

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


class PlayerSerializer(serializers.ModelSerializer):
    """Player serializer."""

    track = serializers.SerializerMethodField()
    current_volume = serializers.FloatField(source="volume")
    timestamp = serializers.IntegerField(source="current_progress_timestamp")
    progress_ms = serializers.IntegerField(source="current_progress_ms")
    duration_ms = serializers.IntegerField(source="current_track_duration_ms")

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
