import os

from django.conf import settings
from django.core.files import locks

from cron.backends.lock.base import DjangoCronJobLock


class FileLock(DjangoCronJobLock):
    """Lock backend using the file system.."""

    __lock_fd = None

    def lock(self):
        """Create a file lock."""
        lock_name = self.get_and_create_lock_file_path()
        try:
            self.__lock_fd = open(lock_name, "w+b", 1)
            locks.lock(self.__lock_fd, locks.LOCK_EX | locks.LOCK_NB)
        except IOError:
            return False
        return True

    def release(self):
        """Remove the file to unlock."""
        locks.unlock(self.__lock_fd)
        self.__lock_fd.close()

    def get_lock_file_name(self):
        """Retrieve the file name of the lock file."""
        return f"{self.job_name}.lock"

    def get_and_create_lock_file_path(self):
        """Create the directory for the lock file and return the full file path."""
        default_path = "/tmp"
        path = getattr(settings, "DJANGO_CRON_LOCKFILE_PATH", default_path)
        if not os.path.isdir(path):
            # let it die if failed, can't run further anyway
            os.makedirs(path, exist_ok=True)

        return os.path.join(path, self.get_lock_file_name())
