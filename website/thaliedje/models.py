import os

from django.db import models
from django.conf import settings
from django.urls import reverse
from guardian.shortcuts import get_objects_for_user
from spotipy import SpotifyOAuth
from spotipy.client import Spotify
from users.models import User
from venues.models import Venue


class Player(models.Model):
    """
    Player model for Spotify players.

    Thaliedje can be authorized to access multiple Spotify accounts via the Spotify API.
    The Spotify account model contains data of the authorized accounts. Each account can
    be added to a venue to provide a music player for that venue. This expects a Spotify
    client (playback device) is playing in that venue. Communication happens via the
    Spotipy library, hence authorization works via cache files. These objects are often
    referenced to as Spotify players.
    """

    SCOPE = (
        "user-read-playback-state, "
        "user-modify-playback-state, "
        "user-read-currently-playing, "
        "streaming, app-remote-control"
    )  # The required Spotify API permissions

    display_name = models.CharField(max_length=255, default="", blank=True)
    playback_device_id = models.CharField(max_length=255, default="", blank=True)
    playback_device_name = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text=(
            "When configuring this Spotify account for the first time, make sure to have"
            " the Spotify accounnt active on at least one playback device to complete"
            " configuration."
        ),
    )
    client_id = models.CharField(max_length=255, unique=True)
    client_secret = models.CharField(max_length=255)
    redirect_uri = models.CharField(max_length=255)
    venue = models.OneToOneField(Venue, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        """Meta class."""

        verbose_name = "Player"
        verbose_name_plural = "Players"

        permissions = [
            ("can_control", "Can control music players"),
            ("can_request", "Can request songs"),
        ]

    def __str__(self):
        """
        Convert this object to string.

        :return: the display name if it is not None, the client id otherwise
        """
        if self.display_name is not None:
            return self.display_name
        else:
            return self.client_id

    def get_absolute_url(self):
        """Get the front-end url for a Player."""
        return reverse("thaliedje:now_playing", args=[self.venue])

    @staticmethod
    def get_player(venue):
        """Get a Player for a venue (if it exists)."""
        try:
            return Player.objects.get(venue=venue)
        except Player.DoesNotExist:
            return None

    @property
    def configured(self):
        """Check if this object is ready to play music (a playback device is set)."""
        return self.playback_device_id is not None

    @property
    def cache_path(self):
        """
        Get the Spotipy cache file path for this auth object.

        :return: the cache file path
        """
        if not os.path.exists(settings.SPOTIFY_CACHE_PATH):
            os.makedirs(settings.SPOTIFY_CACHE_PATH)
        return os.path.join(settings.SPOTIFY_CACHE_PATH, self.client_id)

    @property
    def auth(self):
        """
        Get a spotipy SpotifyOAuth object from this database object.

        :return: a spotipy SpotifyOAuth object
        """
        return SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            cache_path=self.cache_path,
            scope=self.SCOPE,
        )

    @property
    def spotify(self):
        """
        Get a Spotify object with a SpotifyOAuth manager as authentication backend.

        :return: a Spotipy Spotify object
        """
        return Spotify(oauth_manager=self.auth)

    @property
    def get_display_name(self):
        """
        Get the display name of the user.

        :return: the display name of the user authenticated
        """
        if self.display_name is None:
            self.display_name = self.spotify.me()["display_name"]
            self.save()
        return self.display_name

    def get_users_with_request_permissions(self):
        """Get users that have the permission to request songs for this player."""
        users = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "thaliedje.can_request", accept_global_perms=True, with_superuser=True
            ):
                users.append(user)
        return users

    def get_users_with_control_permissions(self):
        """Get users that have the permission to control this player."""
        users = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "thaliedje.can_control", accept_global_perms=True, with_superuser=True
            ):
                users.append(user)
        return users


class SpotifyArtist(models.Model):
    """Spotify Artist model."""

    artist_name = models.CharField(max_length=255, unique=True)
    artist_id = models.CharField(max_length=255)

    def __str__(self):
        """
        Convert this object to string.

        :return: the artist name of this object
        """
        return self.artist_name


class SpotifyTrack(models.Model):
    """Spotify Track model."""

    track_id = models.CharField(max_length=255, unique=True)
    track_name = models.CharField(max_length=255)
    track_artists = models.ManyToManyField(SpotifyArtist)

    def __str__(self):
        """
        Convert this object to string.

        :return: the track name of this object
        """
        return self.track_name

    @property
    def artists(self):
        """Get queryset of track_artists."""
        return self.track_artists.all()


class SpotifyQueueItem(models.Model):
    """
    Spotify Queue Item model.

    SpotifyQueueItems are tracks that are added to the queue of the playback
    device for a Player, requested by a certain user.
    """

    track = models.ForeignKey(
        SpotifyTrack, related_name="queue_items", on_delete=models.SET_NULL, null=True, blank=True
    )
    player = models.ForeignKey(Player, related_name="queue", on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        User, related_name="queue_items", null=True, on_delete=models.SET_NULL, blank=True
    )

    class Meta:
        """Meta class."""

        ordering = ["-added"]
