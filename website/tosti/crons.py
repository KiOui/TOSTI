from cron.core import CronJobBase, Schedule

from tosti.services import data_minimisation

WEEKDAYS = [0, 1, 2, 3, 4]
WEEKENDS = [5, 6]


class DataMinimisationCronJob(CronJobBase):
    """Stop the music at a specific time every day."""

    RUN_AT_TIMES = ["00:00"]
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_at_times=RUN_AT_TIMES, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "tosti.dataminimisation"

    def do(self):
        """Minimise data in the database."""
        data_minimisation(dry_run=False)
