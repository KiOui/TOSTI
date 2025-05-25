import abc
import logging
from dataclasses import dataclass, field
from datetime import timedelta
import traceback
import time
import sys
from typing import TextIO

from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now as utc_now
from django.db.models import Q

from cron.helpers import get_class, run_at_time_localized

DEFAULT_LOCK_BACKEND = "cron.backends.lock.cache.CacheLock"
DJANGO_CRON_OUTPUT_ERRORS = False
logger = logging.getLogger("cron")


class BadCronJobError(AssertionError):
    """Error thrown when a cron job is defined in a wrong way."""

    pass


@dataclass
class Schedule:
    """Schedule data class."""

    run_every_mins: int = None
    run_at_times: list[str] = field(default_factory=lambda: [])
    retry_after_failure_mins: int = None
    run_weekly_on_days: list[int] = None
    run_monthly_on_days: list[int] = None
    run_tolerance_seconds: int = 0


class CronJobBase(abc.ABC):
    """
    Base class of a cron job.

    Sub-classes should have the following properties:
    + code - This should be a code specific to the cron being run. Eg. 'general.stats' etc.
    + schedule

    And the following functions:
    + do - This is the actual business logic to be run at the given schedule
    """

    code: str = None
    schedule: Schedule = None

    remove_successful_cron_logs = False

    @abc.abstractmethod
    def do(self):
        """Execute the cron job."""
        raise NotImplementedError("Subclasses must implement this method.")

    @classmethod
    def get_time_until_run(cls) -> timedelta:
        """Get the amount of time until the next run can be executed."""
        from cron.models import CronJobLog

        try:
            last_job = CronJobLog.objects.filter(code=cls.code).latest("start_time")
        except CronJobLog.DoesNotExist:
            return timedelta()
        return (
            last_job.start_time
            + timedelta(minutes=cls.schedule.run_every_mins)
            - utc_now()
        )

    @property
    def id(self) -> str:
        """Retrieve the ID of this cron job."""
        return self.__name__


class CronJobManager:
    """
    Manager to run cron jobs.

    A manager instance should be created per cron job to be run.

    Does all the logger tracking etc. for it. Used as a context manager via 'with' statement to ensure proper logger in
    cases of job failure.
    """

    def __init__(
        self,
        cron_job_class: type(CronJobBase),
        silent: bool = False,
        dry_run: bool = False,
        stdout: TextIO = None,
    ):
        """Initialize a CronJobManager."""
        from cron.models import CronJobLog

        if not issubclass(cron_job_class, CronJobBase):
            raise BadCronJobError(
                "The cron job to be run must be a subclass of {}".format(
                    CronJobBase.__name__
                )
            )

        if cron_job_class.code is None:
            raise BadCronJobError(
                f"Cron class '{cron_job_class.id}' does not have a code attribute"
            )

        if cron_job_class.schedule is None:
            raise BadCronJobError(
                f"Cron class '{cron_job_class.id}' does not have a schedule attribute"
            )

        self.cron_job_class = cron_job_class
        self.lock_class = self.get_lock_class()

        self.cron_log = CronJobLog(start_time=timezone.now())

        self.silent: bool = silent
        self.dry_run: bool = dry_run
        self.stdout: TextIO = stdout or sys.stdout

        self.previously_ran_successful_cron = None
        self.messages: list[str] = []
        self.user_time = None

    @staticmethod
    def should_write_log() -> bool:
        """Whether logging should be written to the console."""
        return getattr(settings, "DJANGO_CRON_OUTPUT_ERRORS", DJANGO_CRON_OUTPUT_ERRORS)

    def should_run_now(self, force: bool = False):
        """Whether the cron job should run at this moment in time."""
        from cron.models import CronJobLog

        self.previously_ran_successful_cron = None
        self.user_time = None

        # If we pass --force options, we force cron run
        if force:
            return True

        current_time = timezone.now()

        if self.cron_job_class.schedule.run_monthly_on_days is not None:
            if current_time.day not in self.cron_job_class.schedule.run_monthly_on_days:
                return False

        if self.cron_job_class.schedule.run_weekly_on_days is not None:
            if (
                not current_time.weekday()
                in self.cron_job_class.schedule.run_weekly_on_days
            ):
                return False

        if self.cron_job_class.schedule.retry_after_failure_mins:
            # We check last job - success or not
            last_job = (
                CronJobLog.objects.filter(code=self.cron_job_class.code)
                .order_by("-start_time")
                .exclude(start_time__gt=current_time)
                .first()
            )
            if (
                last_job
                and not last_job.is_success
                and current_time
                + timedelta(seconds=self.cron_job_class.schedule.run_tolerance_seconds)
                <= last_job.start_time
                + timedelta(
                    minutes=self.cron_job_class.schedule.retry_after_failure_mins
                )
            ):
                return False

        if self.cron_job_class.schedule.run_every_mins is not None:
            try:
                latest_previous_successful_run = (
                    CronJobLog.objects.filter(
                        code=self.cron_job_class.code, is_success=True
                    )
                    .filter(start_time__lt=current_time)
                    .latest("start_time")
                )
            except CronJobLog.DoesNotExist:
                # There is no previously successful run so we run it now.
                return True

            if current_time + timedelta(
                seconds=self.cron_job_class.schedule.run_tolerance_seconds
            ) > latest_previous_successful_run.start_time + timedelta(
                minutes=self.cron_job_class.schedule.run_every_mins
            ):
                return True

        if self.cron_job_class.schedule.run_at_times:
            for time_data in self.cron_job_class.schedule.run_at_times:
                localized_time_data = time.strptime(
                    run_at_time_localized(time_data), "%H:%M"
                )
                actual_time = time.strptime(
                    "{}:{}".format(
                        timezone.localtime(current_time).hour,
                        timezone.localtime(current_time).minute,
                    ),
                    "%H:%M",
                )
                if actual_time >= localized_time_data:
                    qset = CronJobLog.objects.filter(
                        code=self.cron_job_class.code,
                        ran_at_time=time_data,
                        is_success=True,
                    ).filter(
                        Q(start_time__gt=current_time)
                        | Q(
                            end_time__gte=current_time.replace(
                                hour=0, minute=0, second=0, microsecond=0
                            )
                        )
                    )
                    if not qset:
                        self.user_time = time_data
                        return True
        return False

    def make_log(self, messages: list[str], success: bool = True) -> None:
        """Create and log a message."""
        self.cron_log.code = self.cron_job_class.code

        self.cron_log.is_success = success
        self.cron_log.message = self.make_log_msg(messages)
        self.cron_log.ran_at_time = self.user_time
        self.cron_log.end_time = timezone.now()
        self.cron_log.save()

        if not self.cron_log.is_success and CronJobManager.should_write_log():
            logger.error(
                f"{self.cron_log.code} cronjob error:\n{self.cron_log.message}"
            )

    @staticmethod
    def make_log_msg(messages: list[str]) -> str:
        """Make one string out of multiple log messages."""
        full_message = ""
        if messages:
            for message in messages:
                if len(message):
                    full_message += message
                    full_message += "\n"

        return full_message

    def __enter__(self):
        """Update the start_time of the cron log."""
        self.cron_log.start_time = timezone.now()
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        """Log if exit with exception."""
        if ex_type is None:
            return True

        non_logging_exceptions = [BadCronJobError, self.lock_class.LockFailedException]

        if ex_type in non_logging_exceptions:
            if not self.silent:
                self.stdout.write("{0}\n".format(ex_value))
                logger.info(ex_value)
        else:
            if not self.silent:
                self.stdout.write(
                    "[\N{HEAVY BALLOT X}] {0}\n".format(self.cron_job_class.code)
                )
            try:
                trace = "".join(
                    traceback.format_exception(ex_type, ex_value, ex_traceback)
                )
                self.make_log(self.messages + [trace], success=False)
            except Exception as e:
                err_msg = (
                    f"Error saving cronjob ({self.cron_job_class.id}) log message: {e}"
                )
                logger.error(err_msg)

        return True  # prevent exception propagation

    def run(self, force=False):
        """Schedule a do() call on a CronJobBase object."""
        with self.lock_class(self.cron_job_class, self.silent):
            if self.should_run_now(force):
                if not self.dry_run:
                    cron_job = self.cron_job_class()
                    logger.debug(
                        f"Running cron: {self.cron_job_class.id} code {self.cron_job_class.code}"
                    )
                    self.make_log(["Job in progress"], success=True)
                    self.messages: list[str] = cron_job.do()
                    self.make_log(self.messages, success=True)
                if not self.silent:
                    self.stdout.write(
                        f"[\N{HEAVY CHECK MARK}] {self.cron_job_class.code}\n"
                    )
                self._remove_old_success_job_logs(self.cron_job_class)
            elif not self.silent:
                self.stdout.write(f"[ ] {self.cron_job_class.code}\n")

    @staticmethod
    def get_lock_class():
        """Retrieve the lock backend."""
        name = getattr(settings, "DJANGO_CRON_LOCK_BACKEND", DEFAULT_LOCK_BACKEND)
        try:
            return get_class(name)
        except Exception as err:
            raise Exception(f"invalid lock module {name}. Can't use it: {err}")

    def _remove_old_success_job_logs(self, job_class: type(CronJobBase)):
        """Remove old successful cron job logs if necessary."""
        if job_class.remove_successful_cron_logs or getattr(
            settings, "REMOVE_SUCCESSFUL_CRON_LOGS", False
        ):
            from cron.models import CronJobLog

            CronJobLog.objects.filter(code=job_class.code, is_success=True).exclude(
                pk=self.cron_log.pk
            ).delete()
