from datetime import datetime, timedelta


class CacheInstance:
    """Class for storing cache instances."""

    def __init__(self, value, cache_valid_time_ms):
        """Initialize."""
        self.valid_until = datetime.now() + timedelta(milliseconds=cache_valid_time_ms)
        self.value = value

    def is_valid(self) -> bool:
        """Check whether cache is still valid."""
        return self.valid_until > datetime.now()


class Cache:
    """Class for caching responses."""

    def __init__(self):
        """Initialize."""
        self._instance_cache = dict()

    def reset(self):
        """Reset all cache."""
        self._instance_cache = dict()

    def check_cache(self, cache_id: str) -> (bool, any):
        """
        Check the cache for possibly cached data.

        :param cache_id: the identifier to check cache for
        :return a tuple with the first argument a boolean whether the cache was hit and the second argument the
        possibly cached data
        """
        if cache_id in self._instance_cache.keys():
            cache_instance = self._instance_cache[cache_id]
            if cache_instance.is_valid():
                return True, cache_instance.value
        return False, None

    def update_cache(self, cache_id: str, value, valid_ms):
        """
        Update the cache with new data.

        :param cache_id: the identifier to store cache to
        :param value: the value to set the cache to
        :param valid_ms: the time in milliseconds that cache is valid
        """
        self._instance_cache[cache_id] = CacheInstance(value, valid_ms)

    def call_method_cached(
        self, method, cache_id: str, check_cache: bool, store_cache: bool, valid_ms=5000, reset_cache: bool = False
    ):
        """
        Call a method and check and store cached data.

        :param method: the method to call
        :param cache_id: the identifier for the cache
        :param check_cache: whether to check cache
        :param store_cache: whether to store cache
        :param valid_ms: the time in milliseconds that cache is valid
        :param reset_cache: whether to reset cache after a successful call
        """
        if check_cache:
            hit, cache_value = self.check_cache(cache_id)
            if hit:
                if reset_cache:
                    self.reset()
                return cache_value
        result = method()
        if reset_cache:
            self.reset()
        if store_cache:
            self.update_cache(cache_id, result, valid_ms)
        return result
