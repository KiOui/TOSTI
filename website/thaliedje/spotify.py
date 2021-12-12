import inspect

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

    def currently_playing(self, player: Player, check_cache=True, store_cache=True):
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
        return self.cache.call_method_cached(
            player.spotify.currently_playing,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
        )

    def pause_playback(self, player: Player, check_cache=True, store_cache=True):
        """Pause playback."""
        return self.cache.call_method_cached(
            player.spotify.pause_playback,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            valid_ms=1000,
            reset_cache=True,
        )

    def start_playback(self, player: Player, check_cache=True, store_cache=True):
        """Start playback."""
        return self.cache.call_method_cached(
            player.spotify.start_playback,
            "{}_{}".format(player.id, inspect.currentframe().f_code.co_name),
            check_cache,
            store_cache,
            valid_ms=1000,
            reset_cache=True,
        )
