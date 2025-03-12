from django.conf import settings

from cron.core import CronJobBase, Schedule, get_class
from cron.models import CronJobLog
from tosti.services import send_email


class FailedRunsNotificationCronJob(CronJobBase):
    """Send email if cron failed to run X times in a row."""

    RUN_EVERY_MINS = 30

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "cron.FailedRunsNotificationCronJob"

    def do(self):
        """Notify with an email."""
        crons_to_check = [get_class(x) for x in settings.CRON_CLASSES]
        emails = [admin[1] for admin in settings.ADMINS]

        failed_runs_cronjob_email_prefix = getattr(settings, "FAILED_RUNS_CRONJOB_EMAIL_PREFIX", "")

        for cron in crons_to_check:

            min_failures = getattr(cron, "MIN_NUM_FAILURES", 10)
            jobs = CronJobLog.objects.filter(code=cron.code).order_by("-end_time")[:min_failures]
            failures = 0
            message = ""

            for job in jobs:
                if not job.is_success:
                    failures += 1
                    message += f"Job ran at {job.start_time} : \n\n {job.message} \n\n"

            if failures >= min_failures:
                send_email(
                    f"{failed_runs_cronjob_email_prefix}{cron.code} failed {min_failures} times in a row!",
                    message,
                    emails,
                    text_content=message,
                )
