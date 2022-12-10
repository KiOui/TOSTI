import os
import secrets
import uuid

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinLengthValidator
from django.db import models
from django.conf import settings
from django.db.models import When, F, Case
from django.urls import reverse
from django.utils import timezone
from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import RangeCheckProperty, AnnotationProperty, queryable_property
from spotipy import SpotifyOAuth
from spotipy.client import Spotify

from associations.models import Association
from users.models import User
from venues.models import Venue, Reservation


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
    slug = models.SlugField(unique=True, max_length=100)
    playback_device_id = models.CharField(max_length=255, default="", blank=True)
    playback_device_name = models.CharField(
        max_length=255,
        default="",
        blank=True,
        help_text=(
            "When configuring this Spotify account for the first time, make sure to have"
            " the Spotify account active on at least one playback device to complete"
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
            ("can_request_playlists_and_albums", "Can request playlists and albums"),
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
        return (
            reverse("thaliedje:now_playing", args=[self.venue])
            if self.venue
            else reverse("thaliedje:now_playing", args=[self])
        )

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


class SpotifyArtist(models.Model):
    """Spotify Artist model."""

    artist_name = models.CharField(max_length=255)
    artist_id = models.CharField(max_length=255, unique=True)

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


class ThaliedjeBlacklistedUser(models.Model):
    """Model for blacklisted users."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        """Print object as a string."""
        return f"{self.user} blacklisted for requesting songs"

    class Meta:
        """Meta class for ThaliedjeBlacklistedUser."""

        verbose_name = "blacklisted user"


class ThaliedjeControlEvent(models.Model):
    """Model for setting different control permissions during a certain time period."""

    event = models.OneToOneField(Reservation, on_delete=models.CASCADE, null=False, blank=False)

    association_can_request = models.BooleanField(default=False)
    association_can_control = models.BooleanField(default=False)
    association_can_request_playlist = models.BooleanField(default=False)

    selected_users = models.ManyToManyField(User, blank=True, related_name="thaliedje_control_events")
    join_code = models.CharField(max_length=255, blank=True, null=True, validators=[MinLengthValidator(20)])
    selected_users_can_request = models.BooleanField(default=False)
    selected_users_can_control = models.BooleanField(default=False)
    selected_users_can_request_playlist = models.BooleanField(default=False)

    everyone_can_request = models.BooleanField(default=False)
    everyone_can_control = models.BooleanField(default=False)
    everyone_can_request_playlist = models.BooleanField(default=False)

    respect_blacklist = models.BooleanField(default=True)

    start = AnnotationProperty(F("event__start"))
    end = AnnotationProperty(F("event__end"))

    active = RangeCheckProperty("event__start", "event__end", timezone.now)

    objects = QueryablePropertiesManager()

    @queryable_property
    def player(self):
        """Get the player for this event."""
        return self.event.venue.player

    @player.annotater
    @classmethod
    def player(cls):
        """Get the player for this event."""
        return F("event__venue__player")

    @queryable_property
    def association(self):
        """Get the player for this event."""
        return self.event.association

    @association.annotater
    @classmethod
    def association(cls):
        """Get the player for this event."""
        return F("event__association")

    @property
    def admins(self):
        """Get the admins for this event."""
        return self.event.users_access.all()

    @property
    def event_logs(self):
        """Get the event logs for this event."""
        return self.player.logs.filter(timestamp__range=(self.start, self.end))

    def can_control_player(self, user):
        """Check if a user can control the player."""
        if self.everyone_can_control and user.is_authenticated:
            return True
        if (
            self.association_can_control
            and user.is_authenticated
            and self.association is not None
            and user.association == self.association
        ):
            return True
        if self.selected_users_can_control and user in self.selected_users.all():
            return True
        if user in self.admins.all():
            return True
        return False

    def can_request_song(self, user):
        """Check if a user can request a song."""
        if self.everyone_can_request and user.is_authenticated:
            return True
        if (
            self.association_can_request
            and user.is_authenticated
            and self.association is not None
            and user.association == self.association
        ):
            return True
        if self.selected_users_can_request and user in self.selected_users.all():
            return True
        if user in self.admins.all():
            return True
        return False

    def can_request_playlist(self, user):
        """Check if a user can request a playlist."""
        if self.everyone_can_request_playlist and user.is_authenticated:
            return True
        if (
            self.association_can_request_playlist
            and user.is_authenticated
            and self.association is not None
            and user.association == self.association
        ):
            return True
        if self.selected_users_can_request_playlist and user in self.selected_users.all():
            return True
        if user in self.admins.all():
            return True
        return False

    def get_absolute_url(self):
        """Get the absolute url for this event."""
        return reverse("thaliedje:event-control", kwargs={"pk": self.pk})

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save the reservation."""
        if not self.join_code:
            self.join_code = secrets.token_urlsafe(20)

        if self.association_can_request_playlist:
            self.association_can_request = True
        if self.selected_users_can_request_playlist:
            self.selected_users_can_request = True
        if self.everyone_can_request_playlist:
            self.everyone_can_request = True

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        """Convert this object to string."""
        return f"Control event for {self.event}"

    class Meta:
        """Meta class for ThaliedjeControlEvent."""

        verbose_name = "control event"
        verbose_name_plural = "control events"


class PlayerLogEntry(models.Model):
    """Model for logging player events."""

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="logs")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        """Print object as a string."""
        return f"{self.player} {self.action} by {self.user} at {self.timestamp}"

    class Meta:
        """Meta class for PlayerLogEntry."""

        verbose_name = "player log entry"
        verbose_name_plural = "player log entries"
