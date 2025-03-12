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
    code = "test_run_at_times"
    schedule = Schedule(run_at_times=["0:00", "0:05"])

    def do(self):
        """Do nothing."""
        pass


class Wait3secCronJob(CronJobBase):
    code = "test_wait_3_seconds"
    schedule = Schedule(run_every_mins=5)

    def do(self):
        """Sleep."""
        sleep(3)


class RunOnWeekendCronJob(CronJobBase):
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
    code = "run_on_month_days"
    schedule = Schedule(
        run_monthly_on_days=[1, 10, 20],
        run_at_times=[
            "0:00",
        ],
    )

    def do(self):
        pass


class RunEveryMinuteAndRemoveOldLogs(CronJobBase):
    code = "run_and_remove_old_logs"
    schedule = Schedule(run_every_mins=1)
    remove_successful_cron_logs = True

    def do(self):
        pass
