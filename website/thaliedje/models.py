import logging
import os
import secrets
import time
from datetime import timedelta

from constance import config
from django.templatetags.static import static
from django.core.cache import cache
from django.core.validators import MinLengthValidator
from django.db import models
from django.conf import settings
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.utils.datetime_safe import datetime
from model_utils.managers import InheritanceManager
from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import RangeCheckProperty, AnnotationProperty, queryable_property
from requests import ReadTimeout
from spotipy import SpotifyOAuth, SpotifyException
from spotipy.client import Spotify

from thaliedje.marietje import Marietje, MarietjeClientCredentials, MarietjeException
from users.models import User
from venues.models import Venue, Reservation


class Player(models.Model):
    """A player."""

    display_name = models.CharField(max_length=255, default="", blank=True)
    slug = models.SlugField(unique=True, max_length=100)
    venue = models.OneToOneField(Venue, on_delete=models.SET_NULL, null=True, blank=True)

    objects = InheritanceManager()

    def __str__(self):
        """Get the string representation of a Player."""
        if self.display_name is not None:
            return self.display_name
        else:
            return self.venue.name

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
    def current_image(self):
        """Get the image for the currently playing song."""
        raise NotImplementedError

    @property
    def current_track_name(self):
        """Get the track name for the currently playing song."""
        raise NotImplementedError

    @property
    def current_artists(self):
        """Get the artist names for the currently playing song."""
        raise NotImplementedError

    @property
    def is_playing(self):
        """Check if the player is currently playing music."""
        raise NotImplementedError

    @property
    def current_timestamp(self):
        """Get the timestamp of the latest update with the player."""
        raise NotImplementedError

    @property
    def current_progress_ms(self):
        """Get the current progress of the currently playing song at the current_timestamp."""
        raise NotImplementedError

    @property
    def current_track_duration_ms(self):
        """Get the duration of the currently playing song."""
        raise NotImplementedError

    @property
    def queue(self):
        """Get the queue for this player."""
        raise NotImplementedError

    def request_song(self, track_id):
        """Request a song."""
        raise NotImplementedError

    def start_playing(self, context_uri):
        """Start the player."""
        raise NotImplementedError

    def start(self):
        """Start the player."""
        raise NotImplementedError

    def pause(self):
        """Pause the player."""
        raise NotImplementedError

    def next(self):
        """Skip to the next song."""
        raise NotImplementedError

    def previous(self):
        """Skip to the previous song."""
        raise NotImplementedError

    @property
    def volume(self):
        """Get the volume of the player."""
        raise NotImplementedError

    @volume.setter
    def volume(self, volume):
        """Set the volume of the player."""
        raise NotImplementedError

    @property
    def shuffle(self):
        """Check if the player is in shuffle mode."""
        raise NotImplementedError

    @shuffle.setter
    def shuffle(self, value):
        """Set the shuffle mode of the player."""
        raise NotImplementedError

    @property
    def repeat(self):
        """Get the repeat mode of the player."""
        raise NotImplementedError

    @repeat.setter
    def repeat(self, value):
        """Set the repeat mode of the player."""
        raise NotImplementedError

    def search(self, query, maximum=5, query_type="track"):
        """Search for a song."""
        raise NotImplementedError

    class Meta:
        """Meta class."""

        verbose_name = "Player"
        verbose_name_plural = "Players"
        permissions = [
            ("can_control", "Can control music players"),
            ("can_request_playlists_and_albums", "Can request playlists and albums"),
        ]

    def log_action(self, user, action, description):
        """
        Log a player action.

        :param user: the user
        :param action: the action
        :param description: the description
        """
        PlayerLogEntry.objects.create(
            player=self,
            user=user,
            action=action,
            description=description,
        )

    @property
    def active_control_event(self):
        """Get the active control event for this player."""
        return ThaliedjeControlEvent.current_event(self) or None

    def can_request_playlist(self, user):
        """Check if a user can request playlists or albums."""
        if not user.is_authenticated:
            return False
        control_event = self.active_control_event
        if control_event is not None:
            if control_event.respect_blacklist and ThaliedjeBlacklistedUser.user_is_blacklisted(user):
                return False
            return control_event.can_request_playlist(user)
        return user.has_perm(
            "thaliedje.can_request_playlists_and_albums", self
        ) and not ThaliedjeBlacklistedUser.user_is_blacklisted(user)

    def user_is_throttled(self, user):
        """Check if a user is throttled."""
        if (
            SpotifyQueueItem.objects.filter(requested_by=user, added__gte=timezone.now() - timedelta(hours=1)).count()
            >= config.THALIEDJE_MAX_SONG_REQUESTS_PER_HOUR
        ):
            return True
        return False

    def can_request_song(self, user):
        """Check if a user can request a song."""
        if not user.is_authenticated:
            return False

        control_event = self.active_control_event
        if control_event is not None:
            if control_event.respect_blacklist and ThaliedjeBlacklistedUser.user_is_blacklisted(user):
                return False
            if control_event.check_throttling and self.user_is_throttled(user):
                return False
            return control_event.can_request_song(user)
        return not ThaliedjeBlacklistedUser.user_is_blacklisted(user) and not self.user_is_throttled(user)

    def can_control(self, user):
        """Check if a user can control the player."""
        if not user.is_authenticated:
            return False
        control_event = self.active_control_event
        if control_event is not None:
            if control_event.respect_blacklist and ThaliedjeBlacklistedUser.user_is_blacklisted(user):
                return False
            return control_event.can_control_player(user)
        return user.has_perm("thaliedje.can_control", self) and not ThaliedjeBlacklistedUser.user_is_blacklisted(user)


class MarietjePlayer(Player):
    """A player that is controlled by Marietje."""

    url = models.URLField(max_length=255, default="", blank=False, null=False)
    client_id = models.CharField(max_length=100, blank=False, null=False)
    client_secret = models.CharField(max_length=255, blank=False, null=False)

    @property
    def cache_path(self):
        """
        Get the Spotipy cache file path for this auth object.

        :return: the cache file path
        """
        if not os.path.exists(settings.MARIETJE_CACHE_PATH):
            os.makedirs(settings.MARIETJE_CACHE_PATH)
        return os.path.join(settings.MARIETJE_CACHE_PATH, self.client_id)

    @property
    def auth(self):
        """Get Marietje Auth credentials."""
        return MarietjeClientCredentials(self.url, self.client_id, self.client_secret, cache_path=self.cache_path)

    @property
    def marietje(self):
        """Get a Marietje client."""
        return Marietje(self.url, auth_manager=self.auth)

    def do_marietje_request(self, func, *args, **kwargs):
        """
        Perform a Marietje request with error handling.

        :param func: the function to call
        :param args: the arguments to pass to the function
        :param kwargs: the keyword arguments to pass to the function
        :return: the result of the function call
        """
        logging.info("Performing Marietje request: %s", func.__name__)

        try:
            return func(*args, **kwargs)
        except MarietjeException as e:
            logging.warning("Marietje error: %s", e)
            return None
        except ReadTimeout:
            logging.warning("Marietje request timed out.")
            return None

    @property
    def _current_playback_cache_key(self):
        """Get the cache key for the current playback cache."""
        return f"marietje_player_{self.id}_playback"

    def _get_current_playback(self):
        """Add a timestamp to the marietje requests."""
        before_call = time.time() * 1000

        marietje_response = self.do_marietje_request(self.marietje.queue_current)

        after_call = time.time() * 1000
        if marietje_response is not None:
            marietje_response["timestamp"] = int((before_call + after_call) / 2)
        return marietje_response

    def _current_playback(self):
        """Get the current playback from the Marietje API."""
        cached_result = cache.get(self._current_playback_cache_key)
        if cached_result is not None:
            if cached_result == "unavailable":
                return None
            return cached_result

        playback = self._get_current_playback()

        if playback is None:
            cache.set(self._current_playback_cache_key, "unavailable", 5)
            return None

        cache.set(self._current_playback_cache_key, playback, 5)

        return playback

    @property
    def current_image(self):
        """Get the image url for the currently playing song."""
        return str(static("thaliedje/img/marietje-placeholder.png"))

    @property
    def current_track_name(self):
        """Get the track name for the currently playing song."""
        playback = self._current_playback()

        if playback is None:
            return playback

        return playback["current_song"]["song"]["title"]

    @property
    def current_artists(self):
        """Get the artist names for the currently playing song."""
        playback = self._current_playback()

        if playback is None:
            return playback

        return [playback["current_song"]["song"]["artist"]]

    @property
    def current_timestamp(self):
        """Get the timestamp of the latest update with the player."""
        playback = self._current_playback()

        if playback is None:
            return playback

        return playback["timestamp"]

    @property
    def current_progress_ms(self):
        """Get the current progress of the currently playing song at the current_timestamp."""
        playback = self._current_playback()

        if playback is None:
            return playback

        if playback["current_song"]["played_at"] is None:
            return 0

        song_started_at = datetime.fromisoformat(playback["current_song"]["played_at"])
        progress_timedelta = timezone.now() - song_started_at

        return progress_timedelta.total_seconds() * 1000

    @property
    def current_track_duration_ms(self):
        """Get the duration of the currently playing song."""
        playback = self._current_playback()

        if playback is None:
            return playback

        return playback["current_song"]["song"]["duration"] * 1000

    @property
    def _queue_cache_key(self):
        """Get the cache key for the queue."""
        return f"marietje_player_{self.id}_queue"

    @property
    def queue(self):
        """Get the queue for this player."""
        cached_result = cache.get(self._queue_cache_key)
        if cached_result is not None:
            if cached_result == "unavailable":
                return None
            return cached_result

        queue = self.do_marietje_request(self.marietje.queue_current)

        if queue is None:
            cache.set(self._queue_cache_key, "unavailable", 10)

        queue = [
            {
                "track_id": item["song"]["id"],
                "track_name": item["song"]["title"],
                "track_artists": [item["song"]["artist"]],
                "duration_ms": int(item["song"]["duration"]) * 1000,
            }
            for item in queue["queue"]
        ]
        cache.set(self._queue_cache_key, queue, 10)
        return queue

    def get_absolute_url(self):
        """Get the front-end url for a Player."""
        return self.url

    def can_request_playlist(self, user):
        """Check if a user can request playlists or albums."""
        return False

    def can_request_song(self, user):
        """Check if a user can request a song."""
        return False

    def can_control(self, user):
        """Check if a user can control the player."""
        return False

    def request_song(self, track_id):
        """Request a song."""
        pass

    def start_playing(self, context_uri):
        """Start the playing something."""
        pass

    def start(self):
        """Start the player."""
        pass

    def pause(self):
        """Pause the player."""
        pass

    def next(self):
        """Skip to the next song."""
        pass

    def previous(self):
        """Skip to the previous song."""
        pass

    @property
    def is_playing(self):
        """Check if the player is currently playing music."""
        return True

    @property
    def volume(self):
        """Get the volume of the player."""
        return None

    @property
    def shuffle(self):
        """Check if the player is in shuffle mode."""
        return None

    @property
    def repeat(self):
        """Get the repeat mode of the player."""
        return None

    def search(self, query, maximum=5, query_type="track"):
        """Search for a song."""
        pass


class SpotifyPlayer(Player):
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

    class Meta:
        """Meta class."""

        verbose_name = "Spotify player"
        verbose_name_plural = "Spotify players"
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

    def do_spotify_request(self, func, *args, **kwargs):
        """
        Perform a Spotify request with error handling.

        :param func: the function to call
        :param args: the arguments to pass to the function
        :param kwargs: the keyword arguments to pass to the function
        :return: the result of the function call
        """
        if not self.configured:
            raise RuntimeError("This Spotify account is not configured yet.")

        logging.info("Performing Spotify request: %s", func.__name__)

        try:
            return func(*args, **kwargs)
        except SpotifyException as e:
            logging.warning("Spotify error: %s", e)
        except ReadTimeout:
            logging.warning("Spotify request timed out.")

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

    @property
    def _current_playback_cache_key(self):
        """Get the cache key for the current playback cache."""
        return f"spotify_player_{self.id}_playback"

    def _get_current_playback(self):
        """
        Get the current playback from the Spotify API.

        Due to a bug, the API does not return the actual timestamp, so we compute it ourselves.
        """
        before_call = time.time() * 1000

        spotify_response = self.do_spotify_request(self.spotify.current_playback)

        after_call = time.time() * 1000
        if spotify_response is not None:
            spotify_response["timestamp"] = int((before_call + after_call) / 2)
        return spotify_response

    @property
    def _current_playback(self):
        """Get the current playback from the Spotify API."""
        cached_result = cache.get(self._current_playback_cache_key)
        if cached_result is not None:
            if cached_result == "unavailable":
                return None
            return cached_result

        playback = self._get_current_playback()
        if playback is None:
            cache.set(self._current_playback_cache_key, "unavailable", 5)
            return None

        cache.set(self._current_playback_cache_key, playback, 5)
        return playback

    @property
    def _queue_cache_key(self):
        """Get the cache key for the queue."""
        return f"spotify_player_{self.id}_queue"

    @property
    def queue(self):
        """Get the current queue of a player."""
        cached_result = cache.get(self._queue_cache_key)
        if cached_result is not None:
            if cached_result == "unavailable":
                return None
            return cached_result

        queue = self.do_spotify_request(self.spotify.queue)

        queue = [
            {
                "track_id": item["id"],
                "track_name": item["name"],
                "track_artists": self.get_artists_for_spotify_track(item),
                "duration_ms": item["duration_ms"],
            }
            for item in queue["queue"]
        ]

        if queue is None:
            cache.set(self._queue_cache_key, "unavailable", 10)
            return None

        cache.set(self._queue_cache_key, queue, 10)
        return queue

    def request_song(self, track_id):
        """Queue a track."""
        track_info = self.do_spotify_request(self.spotify.track, track_id)

        self.do_spotify_request(self.spotify.add_to_queue, track_id, device_id=self.playback_device_id)

        cache.delete(self._queue_cache_key)

        if not self.is_playing:
            self.start()
            self.next()

        return track_info

    def start_playing(self, context_uri):
        """Start playing something on the playback device of a Player."""
        if self._current_playback is None:
            # If the playback device is not active, make it active
            self.do_spotify_request(self.spotify.transfer_playback, device_id=self.playback_device_id)

        self.do_spotify_request(
            self.spotify.start_playback, device_id=self.playback_device_id, context_uri=context_uri
        )

        cache.delete(self._current_playback_cache_key)

    def start(self):
        """Start playing on the playback device of a Player."""
        if self._current_playback is None:
            # If the playback device is not active, make it active
            self.do_spotify_request(self.spotify.transfer_playback, device_id=self.playback_device_id)

        self.do_spotify_request(self.spotify.start_playback, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)

    def pause(self):
        """Pause the playback device of a Player."""
        self.do_spotify_request(self.spotify.pause_playback, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)

    def next(self):
        """Skip to the next track on the playback device of a Player."""
        self.do_spotify_request(self.spotify.next_track, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)
        cache.delete(self._queue_cache_key)

    def previous(self):
        """Skip to the next track on the playback device of a Player."""
        self.do_spotify_request(self.spotify.previous_track, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)
        cache.delete(self._queue_cache_key)

    @property
    def current_image(self):
        """Get the image for the currently playing song."""
        current_playback = self._current_playback
        if current_playback is None:
            return None
        try:
            return current_playback["item"]["album"]["images"][0]["url"]
        except (KeyError, IndexError, TypeError):
            return None

    @property
    def current_track_name(self):
        """Get the track name for the currently playing song."""
        current_playback = self._current_playback
        if current_playback is None:
            return None
        try:
            return current_playback["item"]["name"]
        except (KeyError, IndexError, TypeError):
            return None

    @property
    def current_artists(self):
        """Get the artist names for the currently playing song."""
        current_playback = self._current_playback
        if current_playback is None:
            return []
        try:
            return self.get_artists_for_spotify_track(self._current_playback["item"])
        except (KeyError, IndexError, TypeError):
            return []

    @property
    def is_playing(self):
        """Check if the player is currently playing music."""
        current_playback = self._current_playback
        if current_playback is None:
            return False
        return current_playback["is_playing"]

    @property
    def current_timestamp(self):
        """Get the timestamp of the latest update with the player."""
        current_playback = self._current_playback
        if current_playback is None:
            return None
        return current_playback["timestamp"]

    @property
    def current_progress_ms(self):
        """Get the current progress of the currently playing song at the current_timestamp."""
        current_playback = self._current_playback
        if current_playback is None:
            return None
        return current_playback["progress_ms"]

    @property
    def current_track_duration_ms(self):
        """Get the duration of the currently playing song."""
        current_playback = self._current_playback
        if current_playback is None or current_playback["item"] is None:
            return None
        return current_playback["item"]["duration_ms"]

    @property
    def volume(self):
        """Get the volume of the playback device of a Player."""
        current_playback = self._current_playback
        if current_playback is None or current_playback["device"] is None:
            return None
        return current_playback["device"]["volume_percent"]

    @staticmethod
    def get_artists_for_spotify_track(spotify_track):
        """Get the artists for a spotify track."""
        try:
            return [x["name"] for x in spotify_track["artists"]]
        except KeyError:
            return []

    @volume.setter
    def volume(self, volume_percent):
        """Set the volume of the playback device of a Player."""
        self.do_spotify_request(self.spotify.volume, volume_percent, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)

    @property
    def shuffle(self):
        """Get whether a player is shuffling."""
        current_playback = self._current_playback
        if current_playback is None:
            return None
        return current_playback["shuffle_state"]

    @shuffle.setter
    def shuffle(self, shuffle_state: bool):
        """Set the shuffle state of the playback device of a Player."""
        self.do_spotify_request(self.spotify.shuffle, shuffle_state, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)
        cache.delete(self._queue_cache_key)

    @property
    def repeat(self):
        """Get the repeat state of the playback device of a Player."""
        current_playback = self._current_playback
        if current_playback is None:
            return None
        return current_playback["repeat_state"]

    @repeat.setter
    def repeat(self, repeat_state: str):
        """Set the repeat state of the playback device of a Player."""
        if repeat_state not in ["off", "track", "context"]:
            raise ValueError("Repeat state must be one of 'off', 'track', or 'context'")
        self.do_spotify_request(self.spotify.repeat, repeat_state, device_id=self.playback_device_id)
        cache.delete(self._current_playback_cache_key)

    def search(self, query, maximum=5, query_type="track"):
        """
        Search SpotifyTracks for a search query.

        :param query: the search query
        :param maximum: the maximum number of results to search for
        :param query_type: the type of the spotify instance to search
        :return: a list of tracks [{"name": the trackname, "artists": [a list of artist names],
         "id": the Spotify track id}]
        """
        results = self.do_spotify_request(self.spotify.search, q=query, limit=maximum, type=query_type)

        if results is None:
            return []

        trimmed_result = dict()

        for key in results.keys():
            # Filter out None values as the Spotipy library might return None for data it can't decode
            trimmed_result_for_key = [x for x in results[key]["items"] if x is not None]
            if key == "tracks":
                trimmed_result_for_key = sorted(trimmed_result_for_key, key=lambda x: -x["popularity"])
                trimmed_result_for_key = [
                    {
                        "type": x["type"],
                        "name": x["name"],
                        "artists": self.get_artists_for_spotify_track(x),
                        "id": x["id"],
                        "uri": x["uri"],
                        "image": x["album"]["images"][0]["url"],
                    }
                    for x in trimmed_result_for_key
                ]
                trimmed_result["tracks"] = trimmed_result_for_key
            elif key == "albums":
                trimmed_result_for_key = [
                    {
                        "type": x["type"],
                        "name": x["name"],
                        "artists": self.get_artists_for_spotify_track(x),
                        "id": x["id"],
                        "uri": x["uri"],
                        "image": x["images"][0]["url"],
                    }
                    for x in trimmed_result_for_key
                ]
                trimmed_result["albums"] = trimmed_result_for_key
            elif key == "playlists":
                trimmed_result_for_key = [
                    {
                        "type": x["type"],
                        "name": x["name"],
                        "owner": x["owner"],
                        "id": x["id"],
                        "uri": x["uri"],
                        "image": x["images"][0]["url"] if len(x["images"]) > 0 else None,
                    }
                    for x in trimmed_result_for_key
                ]
                trimmed_result["playlists"] = trimmed_result_for_key
        return trimmed_result


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

    @classmethod
    def get_or_create_from_spotify(cls, spotify_data):
        """Create a SpotifyArtist object from Spotify data."""
        obj, _ = cls.objects.get_or_create(artist_id=spotify_data["id"])
        if obj.artist_name != spotify_data["name"]:
            obj.artist_name = spotify_data["name"]
            obj.save()
        return obj


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

    @classmethod
    def get_or_create_from_spotify(cls, spotify_data):
        """Create a SpotifyTrack object from Spotify data."""
        obj, _ = cls.objects.get_or_create(track_id=spotify_data["id"])
        updated = False

        if obj.track_name != spotify_data["name"]:
            obj.track_name = spotify_data["name"]
            updated = True

        artists = (
            [SpotifyArtist.get_or_create_from_spotify(x) for x in spotify_data["artists"]]
            if "artists" in spotify_data.keys()
            else []
        )

        if set(obj.track_artists.all()) != set(artists):
            [obj.track_artists.add(x) for x in artists]
            updated = True

        if updated:
            obj.save()

        return obj


class SpotifyQueueItem(models.Model):
    """
    Spotify Queue Item model.

    SpotifyQueueItems are tracks that are added to the queue of the playback
    device for a Player, requested by a certain user.
    """

    track = models.ForeignKey(SpotifyTrack, related_name="requests", on_delete=models.SET_NULL, null=True, blank=True)
    player = models.ForeignKey(Player, related_name="requests", on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(User, related_name="requests", null=True, on_delete=models.SET_NULL, blank=True)

    @classmethod
    def queue_track(cls, spotify_data, player, user):
        """Add a track to the queue of a player."""
        track = SpotifyTrack.get_or_create_from_spotify(spotify_data)
        return cls.objects.create(track=track, player=player, requested_by=user)

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

    @classmethod
    def user_is_blacklisted(cls, user):
        """Return if the user is on the blacklist."""
        return cls.objects.filter(user=user).exists()

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
    check_throttling = models.BooleanField(default=True)

    start = AnnotationProperty(F("event__start"))
    end = AnnotationProperty(F("event__end"))

    active = RangeCheckProperty("start", "end", timezone.now)

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

    @classmethod
    def current_event(cls, player):
        """
        Get the active ThaliedjeControlEvent for a Player.

        :param player: the player
        :return: the active ThaliedjeControlEvent or None
        """
        try:
            return cls.objects.get(player=player.id, active=True)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            logging.error("Multiple active ThaliedjeControlEvents found for player %s", player)
            return None

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
