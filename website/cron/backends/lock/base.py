from cron.core import CronJobBase


class DjangoCronJobLock:
    """
    The lock class to use in runcrons management command.

    Intended usage is
    with CacheLock(cron_class, silent):
        do work
    or inside try - except:
    try:
        with CacheLock(cron_class, silent):
            do work
    except DjangoCronJobLock.LockFailedException:
        pass
    """

    class LockFailedException(Exception):
        """Exception thrown when the lock failed to acquire."""

        pass

    def __init__(self, cron_class: type(CronJobBase), silent: bool, *args, **kwargs):
        """Initialize the lock."""
        self.job_name: str = ".".join([cron_class.__module__, cron_class.__name__])
        self.job_code: str = cron_class.code
        self.parallel: bool = getattr(cron_class, "ALLOW_PARALLEL_RUNS", False)
        self.silent: bool = silent

    def lock(self):
        """
        Acquire the lock.

        This method is typically called from the __enter__ method. Return True on success, False if the lock could not
        be acquired.

        Here you can optionally call self.notice_lock_failed().
        """
        raise NotImplementedError("You have to implement lock(self) method for your class")

    def release(self):
        """
        Release the lock.

        Typically called from __exit__ method. There is no need to return anything.
        """
        raise NotImplementedError("You have to implement release(self) method for your class")

    def lock_failed_message(self) -> str:
        """Message for when the lock failed to acquire."""
        return f"{self.job_name}: lock found. Will try later."

    def __enter__(self):
        """Try to acquire a lock."""
        if not self.parallel and not self.lock():
            raise self.LockFailedException(self.lock_failed_message())

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock."""
        if not self.parallel:
            self.release()
