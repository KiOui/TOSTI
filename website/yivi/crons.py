from django_cron import CronJobBase, Schedule


class CleanupSessionCronJob(CronJobBase):
    """Cronjob to clean up old Yivi sessions."""

    RUN_EVERY_MINS = 60 * 24
    RETRY_AFTER_FAILURE_MINS = 30
    schedule = Schedule(
        run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS, run_on_days=WEEKDAYS
    )
    code = "yivi.cleanupsessions"

    def do(self):
        """Cleanup sessions."""
        # TODO: write this
        pass
