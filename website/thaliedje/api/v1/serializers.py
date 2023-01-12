from thaliedje.services import player_currently_playing, get_player_volume, get_shuffle, get_repeat
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

    is_playing = serializers.SerializerMethodField()
    shuffle = serializers.SerializerMethodField()
    repeat = serializers.SerializerMethodField()
    track = serializers.SerializerMethodField()
    current_volume = serializers.SerializerMethodField()

    timestamp = serializers.SerializerMethodField()
    progress_ms = serializers.SerializerMethodField()
    duration_ms = serializers.SerializerMethodField()

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

    def get_shuffle(self, instance):
        """Get whether the player is shuffling."""
        return get_shuffle(instance)

    def get_repeat(self, instance):
        """Get whether the player is repeating."""
        return get_repeat(instance)

    def get_timestamp(self, instance):
        """Get timestamp."""
        currently_playing = player_currently_playing(instance)
        if currently_playing:
            return currently_playing["timestamp"]
        else:
            return None

    def get_progress_ms(self, instance):
        """Get progress_ms."""
        currently_playing = player_currently_playing(instance)
        if currently_playing:
            return currently_playing["progress_ms"]
        else:
            return None

    def get_duration_ms(self, instance):
        """Get duration_ms."""
        currently_playing = player_currently_playing(instance)
        if currently_playing:
            return currently_playing["duration_ms"]
        else:
            return None

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
            "shuffle",
            "repeat",
            "current_volume",
            "timestamp",
            "progress_ms",
            "duration_ms",
        ]
