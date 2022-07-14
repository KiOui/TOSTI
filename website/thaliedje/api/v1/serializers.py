from thaliedje.services import player_currently_playing, get_player_volume
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


class AnonymousQueueItemSerializer(serializers.ModelSerializer):
    """Queue Item Serializer."""

    track = TrackSerializer(many=False, read_only=True)

    class Meta:
        """Meta class."""

        model = models.SpotifyQueueItem
        fields = [
            "track",
            "added",
        ]


class QueueItemSerializer(serializers.ModelSerializer):
    """Queue Item Serializer."""

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

    is_playing = serializers.SerializerMethodField()
    track = serializers.SerializerMethodField()
    current_volume = serializers.SerializerMethodField()

    def get_track(self, instance):
        """Get track as a dict."""
        currently_playing = player_currently_playing(instance)
        if currently_playing:
            return {
                "image": currently_playing["image"],
                "name": currently_playing["name"],
                "artists": currently_playing["artists"],
            }
        else:
            return None

    def get_is_playing(self, instance):
        """Get if the player is playing."""
        currently_playing = player_currently_playing(instance)
        return currently_playing is not False and currently_playing["is_playing"]

    def get_current_volume(self, instance):
        """Get current volume."""
        return get_player_volume(instance)

    class Meta:
        """Meta class."""

        model = models.Player
        fields = [
            "id",
            "slug",
            "display_name",
            "venue",
            "track",
            "is_playing",
            "current_volume",
        ]
