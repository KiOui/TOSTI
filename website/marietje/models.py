import os
from django.db import models
from django.conf import settings
from spotipy import SpotifyOAuth
from spotipy.client import Spotify


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
