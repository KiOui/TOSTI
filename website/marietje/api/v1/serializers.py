from users.api.v1.serializers import UserRelatedField
from rest_framework import serializers
from marietje import models


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


class QueueItemSerializer(serializers.ModelSerializer):
    """Queue Item Serializer."""

    track = TrackSerializer(many=False, read_only=True)
    requested_by = UserRelatedField(many=False)

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

    class Meta:
        """Meta class."""

        model = models.Player
        fields = [
            "id",
            "display_name",
            "venue",
        ]


class PlayerRetrieveSerializer(serializers.ModelSerializer):
    """Player Retrieve Serializer."""

    is_playing = serializers.SerializerMethodField()
    track = serializers.SerializerMethodField()

    def get_track(self, instance):
        """Get track as a dict."""
        currently_playing = instance.currently_playing
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
        currently_playing = instance.currently_playing
        return currently_playing is not False and currently_playing["is_playing"]

    class Meta:
        """Meta class."""

        model = models.Player
        fields = [
            "id",
            "display_name",
            "venue",
            "track",
            "is_playing",
        ]
