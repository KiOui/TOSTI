from datetime import datetime

from django.conf import settings
from django.core.cache import caches
from django.utils import timezone

from cron.backends.lock.base import DjangoCronJobLock


class CacheLock(DjangoCronJobLock):
    """Cron Job lock using Django caching."""

    DEFAULT_LOCK_TIME: int = 24 * 60 * 60  # 24 hours

    def __init__(self, cron_class, *args, **kwargs):
        """
        Initialize CacheLock.

        :param cron_class: The class of the cron job. This should be an object that implements CronJobBase.
        """
        super().__init__(cron_class, *args, **kwargs)

        self.cache = self.get_cache_by_name()
        self.lock_name = self.get_lock_name()
        self.timeout = self.get_cache_timeout(cron_class)

    def lock(self) -> bool:
        """This method sets a cache variable to mark current job as "already running"."""
        if self.cache.get(self.lock_name):
            return False
        else:
            self.cache.set(self.lock_name, timezone.now(), self.timeout)
            return True

    def release(self):
        """Release the lock."""
        self.cache.delete(self.lock_name)

    def lock_failed_message(self) -> str:
        """Message for when the lock failed to acquire."""
        started = self.get_running_lock_date()
        return (
            f"{self.job_name}: lock has been found. Other cron started at {started}. Current timeout for job "
            f"{self.job_name} is {self.timeout} seconds (cache key name is '{self.lock_name}')."
        )

    @staticmethod
    def get_cache_by_name():
        """Gets a specified cache (or the `default` cache if CRON_CACHE is not set)."""
        default_cache = "default"
        cache_name = getattr(settings, "DJANGO_CRON_CACHE", default_cache)

        # Allow the possible InvalidCacheBackendError to happen here
        # instead of allowing unexpected parallel runs of cron jobs
        return caches[cache_name]

    def get_lock_name(self) -> str:
        """Retrieve the lock name."""
        return self.job_name

    def get_cache_timeout(self, cron_class) -> int:
        """Retrieve the cache timeout."""
        return getattr(cron_class, "DJANGO_CRON_LOCK_TIME", self.DEFAULT_LOCK_TIME)

    def get_running_lock_date(self) -> datetime:
        date = self.cache.get(self.lock_name)
        if date and not timezone.is_aware(date):
            tz = timezone.get_current_timezone()
            date = timezone.make_aware(date, tz)
        return date
