from datetime import timedelta

from django.utils import timezone
from cron.core import CronJobBase, Schedule

from yivi import models


class CleanupSessionCronJob(CronJobBase):
    """Cronjob to clean up old Yivi sessions."""

    RUN_EVERY_MINS = 60 * 24
    RETRY_AFTER_FAILURE_MINS = 30
    schedule = Schedule(
        run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS
    )
    code = "yivi.cleanupsessions"

    def do(self):
        """Cleanup sessions."""
        cleanup_before_date = timezone.now() - timedelta(days=1)
        models.Session.objects.filter(created_at__lt=cleanup_before_date).delete()
