from time import sleep

from cron.core import CronJobBase, Schedule


class TestSuccessCronJob(CronJobBase):
    """Successful test cron job."""

    code = "test_success_cron_job"
    schedule = Schedule(run_every_mins=0)

    def do(self):
        """Do nothing."""
        pass


class TestErrorCronJob(CronJobBase):
    """Cron job that always results in an error."""

    code = "test_error_cron_job"
    schedule = Schedule(run_every_mins=0)

    def do(self):
        """Throw an error."""
        raise Exception()


class Test5minsCronJob(CronJobBase):
    """Successful cron job that runs every 5 minutes."""

    code = "test_run_every_mins"
    schedule = Schedule(run_every_mins=5)

    def do(self):
        """Do nothing."""
        pass


class Test5minsWithToleranceCronJob(CronJobBase):
    """Successful cron job that runs every 5 minutes with tolerance."""

    code = "test_run_every_mins"
    schedule = Schedule(run_every_mins=5, run_tolerance_seconds=5)

    def do(self):
        """Do nothing."""
        pass


class TestRunAtTimesCronJob(CronJobBase):
    """Cron job that runs at 0:00 and 0:05."""

    code = "test_run_at_times"
    schedule = Schedule(run_at_times=["0:00", "0:05"])

    def do(self):
        """Do nothing."""
        pass


class Wait3secCronJob(CronJobBase):
    """Cron job that sleeps 3 seconds."""

    code = "test_wait_3_seconds"
    schedule = Schedule(run_every_mins=5)

    def do(self):
        """Sleep."""
        sleep(3)


class RunOnWeekendCronJob(CronJobBase):
    """Cron job that only runs on the weekend."""

    code = "run_on_weekend"
    schedule = Schedule(
        run_weekly_on_days=[5, 6],
        run_at_times=[
            "0:00",
        ],
    )

    def do(self):
        """Do nothing."""
        pass


class NoCodeCronJob(CronJobBase):
    """Nothing specified cron job."""

    def do(self):
        """Do nothing."""
        pass


class RunOnMonthDaysCronJob(CronJobBase):
    """Cron job that runs on some days in the month."""

    code = "run_on_month_days"
    schedule = Schedule(
        run_monthly_on_days=[1, 10, 20],
        run_at_times=[
            "0:00",
        ],
    )

    def do(self):
        """Do nothing."""
        pass


class RunEveryMinuteAndRemoveOldLogs(CronJobBase):
    """Cron job that runs every minute and removes old logs."""

    code = "run_and_remove_old_logs"
    schedule = Schedule(run_every_mins=1)
    remove_successful_cron_logs = True

    def do(self):
        """Do nothing."""
        pass
