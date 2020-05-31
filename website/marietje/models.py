import os
from django.db import models
from django.conf import settings
from spotipy import SpotifyOAuth
from spotipy.client import Spotify


class SpotifyAuthCode(models.Model):

    SCOPE = "user-read-playback-state, user-modify-playback-state, user-read-currently-playing, streaming, app-remote-control"

    display_name = models.CharField(max_length=256, null=True)
    client_id = models.CharField(max_length=256, null=False, blank=False, unique=True)
    client_secret = models.CharField(max_length=256, null=False, blank=False)
    redirect_uri = models.CharField(max_length=512, null=False)

    @property
    def cache_path(self):
        return os.path.join(settings.SPOTIFY_CACHE_PATH, self.client_id)

    @property
    def auth(self):
        return SpotifyOAuth(client_id=self.client_id,
                            client_secret=self.client_secret,
                            redirect_uri=self.redirect_uri,
                            cache_path=self.cache_path,
                            scope=self.SCOPE)

    @property
    def spotify(self):
        return Spotify(oauth_manager=self.auth)

    @property
    def get_display_name(self):
        if self.display_name is None:
            self.display_name = self.spotify.me()['display_name']
            self.save()
        return self.display_name
