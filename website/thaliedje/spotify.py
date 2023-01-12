import inspect
import time

from thaliedje.models import Player
from tosti.cache import Cache


class SpotifyCache:
    """Class for caching Spotify responses."""

    _instances = dict()

    def __init__(self, cache: Cache):
        """Initialize."""
        self.cache = cache

    def reset(self):
        """Reset cache."""
        self.cache.reset()

    @staticmethod
    def instance(identifier: int):
        """Get static instance of this class."""
        if identifier not in SpotifyCache._instances.keys():
            SpotifyCache._instances[identifier] = SpotifyCache(Cache())
            return SpotifyCache._instances[identifier]
        else:
            return SpotifyCache._instances[identifier]

    def currently_playing(self, player: Player, check_cache=True, store_cache=True, *args, **kwargs):
        """
        Get the currently playing track information.

        :param player: the player object to retrieve track information for
        :param check_cache: whether to check the cache for cached data first
        :param store_cache: whether to store retrieved data to cache
        :return a dictionary with the following content:
            image: [link to image of track],
            name: [name of currently playing track],
            artists: [list of artist names],
            is_playing: [True|False]
        """

        def _currently_playing(*args, **kwargs):
            # The spotify API doesn't actually return an accurate timestamp,
            # but the timestamp of the latest playback change,
            # so we overwrite it with our own time

            before_call = time.time() * 1000
            spotify_response = player.spotify.currently_playing(*args, **kwargs)
            after_call = time.time() * 1000
            if spotify_response is not None:
                spotify_response["timestamp"] = int((before_call + after_call) / 2)
            return spotify_response

        return self.cache.call_method_cached(
            _currently_playing,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            *args,
            **kwargs,
        )

    def current_playback(self, player: Player, check_cache=True, store_cache=True, *args, **kwargs):
        """
        Get the current playback information.

        :param player: the player object to retrieve track information for
        :param check_cache: whether to check the cache for cached data first
        :param store_cache: whether to store retrieved data to cache
        :return a dictionary with information about the current playback
        """

        def _current_playback(*args, **kwargs):
            # The spotify API doesn't actually return an accurate timestamp,
            # but the timestamp of the latest playback change,
            # so we overwrite it with our own time

            before_call = time.time() * 1000
            spotify_response = player.spotify.current_playback(*args, **kwargs)
            after_call = time.time() * 1000
            if spotify_response is not None:
                spotify_response["timestamp"] = int((before_call + after_call) / 2)
            return spotify_response

        return self.cache.call_method_cached(
            _current_playback,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            *args,
            **kwargs,
        )

    def pause_playback(self, player: Player, check_cache=True, store_cache=True, *args, **kwargs):
        """Pause playback."""
        return self.cache.call_method_cached(
            player.spotify.pause_playback,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            valid_ms=1000,
            reset_cache=True,
            *args,
            **kwargs,
        )

    def start_playback(self, player: Player, check_cache=True, store_cache=True, *args, **kwargs):
        """Start playback."""
        return self.cache.call_method_cached(
            player.spotify.start_playback,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            valid_ms=1000,
            reset_cache=True,
            *args,
            **kwargs,
        )

    def current_queue(self, player, check_cache=True, store_cache=True, *args, **kwargs):
        """Get the current queue."""
        return self.cache.call_method_cached(
            player.spotify.queue,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            *args,
            **kwargs,
        )
