import os

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.urls import reverse
from spotipy import SpotifyOAuth
from spotipy.client import Spotify
from venues.models import Venue

User = get_user_model()


class SpotifyAccount(models.Model):
    """
    SpotifyAccount model for Spotify players.

    Marietje can be authorized to access multiple Spotify accounts via the Spotify API.
    The Spotify account model contains data of the authorized accounts. Each account can
    be added to a venue to provide a music player for that venue. This expects a Spotify
    client (playback device) is playing in that venue. Communciation happens via the
    Spotipy library, hence authorization works via cache files. These objects are often
    referenced to as Spotify players.
    """

    SCOPE = (
        "user-read-playback-state, "
        "user-modify-playback-state, "
        "user-read-currently-playing, "
        "streaming, app-remote-control"
    )  # The required Spotify API permissions

    display_name = models.CharField(max_length=256, null=True, blank=True)
    playback_device_id = models.CharField(max_length=256, null=True, blank=True)
    playback_device_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="When configuring this Spotify account for the first time, "
        "make sure to have the Spotify accounnt active on at least one "
        "playback device to complete configuration.",
    )
    client_id = models.CharField(max_length=256, null=False, blank=False, unique=True)
    client_secret = models.CharField(max_length=256, null=False, blank=False)
    redirect_uri = models.CharField(max_length=512, null=False, blank=False)
    venue = models.OneToOneField(
        Venue, on_delete=models.SET_NULL, null=True, blank=True
    )

    @staticmethod
    def get_player(venue):
        """Get a SpotifyAccount for a venue (if it exists)."""
        try:
            return SpotifyAccount.objects.get(venue=venue)
        except SpotifyAccount.DoesNotExist:
            return None

    @property
    def configured(self):
        """Check if this object is ready to play music (a playback device is set)."""
        return self.playback_device_id is not None

    @property
    def currently_playing(self):
        """
        Get currently playing music information.

        :return: a dictionary with the following content:
        {
            image: [link to image of track],
            name: [name of currently playing track],
            artists: [list of artist names],
            is_playing: [True|False]
        }
        """
        if not self.configured:
            raise RuntimeError("This Spotify account is not configured yet.")

        currently_playing = self.spotify.currently_playing()

        if currently_playing is None:
            return False

        image = currently_playing["item"]["album"]["images"][0]["url"]
        name = currently_playing["item"]["name"]
        artists = [x["name"] for x in currently_playing["item"]["artists"]]

        return {
            "image": image,
            "name": name,
            "artists": artists,
            "is_playing": currently_playing["is_playing"],
        }

    @property
    def cache_path(self):
        """
        Get the Spotipy cache file path for this auth object.

        :return: the cache file path
        """
        return os.path.join(settings.SPOTIFY_CACHE_PATH, self.client_id)

    @property
    def auth(self):
        """
        Get a Spotipy SpotifyOAuth object from this database object.

        :return: a Spotipy SpotifyOAuth object
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

    def get_absolute_url(self):
        """Get the front-end url for a SpotifyAccount."""
        return reverse("marietje:now_playing", args=[self.venue])

    def __str__(self):
        """
        Convert this object to string.

        :return: the display name if it is not None, the client id otherwise
        """
        if self.display_name is not None:
            return self.display_name
        else:
            return self.client_id

    class Meta:
        """Meta class."""

        verbose_name = "Spotify account"
        verbose_name_plural = "Spotify accounts"


class SpotifyArtist(models.Model):
    """Spotify Artist model."""

    artist_name = models.CharField(
        max_length=2048, blank=False, null=False, unique=True
    )
    artist_id = models.CharField(max_length=2048, blank=False, null=False)

    def __str__(self):
        """
        Convert this object to string.

        :return: the artist name of this object
        """
        return self.artist_name


class SpotifyTrack(models.Model):
    """Spotify Track model."""

    track_id = models.CharField(max_length=256, blank=False, null=False, unique=True)
    track_name = models.CharField(max_length=1024, blank=False, null=False)
    track_artists = models.ManyToManyField(SpotifyArtist)

    def __str__(self):
        """
        Convert this object to string.

        :return: the track name of this object
        """
        return self.track_name


class SpotifyQueueItem(models.Model):
    """
    Spotify Queue Item model.

    SpotifyQueueItems are tracks that are added to the queue of the playback
    device for a SpotifyAccount, requested by a certain user.
    """

    track = models.ForeignKey(SpotifyTrack, on_delete=models.SET_NULL, null=True)
    player = models.ForeignKey(SpotifyAccount, null=False, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    class Meta:
        """Meta class."""

        ordering = ["-added"]
