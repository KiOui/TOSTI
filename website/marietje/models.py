import os

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from spotipy import SpotifyOAuth
from spotipy.client import Spotify

User = get_user_model()


class SpotifySettings(models.Model):
    """Spotify Auth model."""

    SCOPE = (
        "user-read-playback-state, "
        "user-modify-playback-state, "
        "user-read-currently-playing, "
        "streaming, app-remote-control"
    )

    display_name = models.CharField(max_length=256, null=True, blank=True)
    playback_device_id = models.CharField(max_length=256, null=True, blank=True)
    playback_device_name = models.CharField(max_length=256, null=True, blank=True)
    client_id = models.CharField(max_length=256, null=False, blank=False, unique=True)
    client_secret = models.CharField(max_length=256, null=False, blank=False)
    redirect_uri = models.CharField(max_length=512, null=False, blank=False)

    @property
    def configured(self):
        """
        Check if this object is ready to play music.

        :return: True if this object is ready for music playback, False otherwise
        """
        return self.playback_device_id is not None

    @property
    def currently_playing(self):
        if not self.configured:
            raise RuntimeError("This Spotify settings object is not configured yet.")

        currently_playing = self.spotify.currently_playing()

        if currently_playing is None:
            return {"image": "", "name": "No currently playing track", "artists": ""}

        image = currently_playing["item"]["album"]["images"][0]["url"]
        name = currently_playing["item"]["name"]
        artists = [x["name"] for x in currently_playing["item"]["artists"]]

        return {"image": image, "name": name, "artists": artists}

    @property
    def cache_path(self):
        """
        Get the cache file path for this auth object.

        :return: the cache file path
        """
        return os.path.join(settings.SPOTIFY_CACHE_PATH, self.client_id)

    @property
    def auth(self):
        """
        Get a SpotifyOAuth object from this database object.

        :return: a SpotifyOAuth object
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

        :return: a Spotify object
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

        verbose_name = "Spotify settings"
        verbose_name_plural = "Spotify settings"


class SpotifyArtist(models.Model):

    artist_name = models.CharField(
        max_length=2048, blank=False, null=False, unique=True
    )
    artist_id = models.CharField(max_length=2048, blank=False, null=False)

    def __str__(self):
        return self.artist_name


class SpotifyTrack(models.Model):

    track_id = models.CharField(max_length=256, blank=False, null=False, unique=True)
    track_name = models.CharField(max_length=1024, blank=False, null=False)
    track_artists = models.ManyToManyField(SpotifyArtist)

    def __str__(self):
        return self.track_name


class SpotifyQueueItem(models.Model):

    track = models.ForeignKey(SpotifyTrack, on_delete=models.SET_NULL, null=True)
    spotify_settings_object = models.ForeignKey(
        SpotifySettings, null=False, on_delete=models.CASCADE
    )
    added = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    class Meta:
        """Meta class."""

        ordering = ["-added"]
