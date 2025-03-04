from cron.backends.lock.base import DjangoCronJobLock
from cron.models import CronJobLock
from django.db import transaction


class DatabaseLock(DjangoCronJobLock):
    """Lock that uses the database."""

    @transaction.atomic
    def lock(self):
        """Set the database object for the cron job to locked."""
        lock, _ = CronJobLock.objects.get_or_create(job_name=self.job_name)
        if lock.locked:
            return False
        else:
            lock.locked = True
            lock.save()
            return True

    @transaction.atomic
    def release(self):
        """Unlock the database object for the cron job."""
        lock, _ = CronJobLock.objects.get_or_create(job_name=self.job_name)
        lock.locked = False
        lock.save()
