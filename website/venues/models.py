from django.db import models
from marietje.models import SpotifySettings


class Venue(models.Model):
    """Venue model class."""

    name = models.CharField(max_length=50, unique=True, blank=False, null=False)
    spotify_player = models.ForeignKey(SpotifySettings, null=True, on_delete=models.SET_NULL, blank=False)
    active = models.BooleanField(default=True, null=False)

    @property
    def has_player(self):
        return self.spotify_player is not None

    def __str__(self):
        """
        Convert this object to string.

        :return: the name of this Venue
        """
        return self.name

    class Meta:
        """Meta class."""

        ordering = ["-active", "name"]
