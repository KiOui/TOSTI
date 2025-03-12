from cron.backends.lock.base import DjangoCronJobLock
from cron.models import CronJobLock
from django.db import transaction


class DatabaseLock(DjangoCronJobLock):
    """
    Locking cron jobs with database. Its good when you have not parallel run and want to make sure 2 jobs won't be
    fired at the same time - which may happened when job execution is longer that job interval.
    """

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
