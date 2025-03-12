import datetime
import threading
from time import sleep
from datetime import timedelta

from unittest.mock import patch

from dateutil.tz import tz
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time

from django import db
from django.test import TransactionTestCase
from django.core.management import call_command
from django.test.utils import override_settings
from django.test.client import Client
from django.urls import reverse

from cron.helpers import humanize_duration
from cron.models import CronJobLog, CronJobLock
from cron.tests.crons import TestErrorCronJob, TestSuccessCronJob, Test5minsCronJob, TestRunAtTimesCronJob


User = get_user_model()


class OutBuffer(object):
    def __init__(self):
        self._str_cache = ""
        self.content = []
        self.modified = False

    def write(self, *args):
        self.content.extend(args)
        self.modified = True

    def str_content(self):
        if self.modified:
            self._str_cache = "".join((str(x) for x in self.content))
            self.modified = False

        return self._str_cache


def call(command, *args, **kwargs):
    """
    Run the runcrons management command with a supressed output.
    """
    out_buffer = OutBuffer()
    call_command(command, *args, stdout=out_buffer, **kwargs)
    return out_buffer.str_content()


class TestRunCrons(TransactionTestCase):
    success_cron = "cron.tests.crons.TestSuccessCronJob"
    error_cron = "cron.tests.crons.TestErrorCronJob"
    five_mins_cron = "cron.tests.crons.Test5minsCronJob"
    five_mins_with_tolerance_cron = "cron.tests.crons.Test5minsWithToleranceCronJob"
    run_at_times_cron = "cron.tests.crons.TestRunAtTimesCronJob"
    wait_3sec_cron = "cron.tests.crons.Wait3secCronJob"
    run_on_wkend_cron = "cron.tests.crons.RunOnWeekendCronJob"
    does_not_exist_cron = "ThisCronObviouslyDoesntExist"
    no_code_cron = "cron.tests.crons.NoCodeCronJob"
    test_failed_runs_notification_cron = "cron.cron.FailedRunsNotificationCronJob"
    run_on_month_days = "cron.tests.crons.RunOnMonthDaysCronJob"
    run_and_remove_old_logs = "cron.tests.crons.RunEveryMinuteAndRemoveOldLogs"

    def _call(self, *args, **kwargs):
        return call("runcrons", *args, **kwargs)

    def setUp(self):
        CronJobLog.objects.all().delete()

    def assertReportedRun(self, job_cls, response):
        expected_log = "[\N{HEAVY CHECK MARK}] {0}".format(job_cls.code)
        self.assertIn(expected_log, response)

    def assertReportedNoRun(self, job_cls, response):
        expected_log = "[ ] {0}".format(job_cls.code)
        self.assertIn(expected_log, response)

    def assertReportedFail(self, job_cls, response):
        expected_log = "[\N{HEAVY BALLOT X}] {0}".format(job_cls.code)
        self.assertIn(expected_log, response)

    def test_success_cron(self):
        self._call(self.success_cron, force=True)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    def test_failed_cron(self):
        response = self._call(self.error_cron, force=True)
        self.assertReportedFail(TestErrorCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    def test_not_exists_cron(self):
        response = self._call(self.does_not_exist_cron, force=True)
        self.assertIn("Make sure these are valid cron class names", response)
        self.assertIn(self.does_not_exist_cron, response)
        self.assertEqual(CronJobLog.objects.all().count(), 0)

    @patch("cron.management.commands.runcrons.logger")
    def test_requires_code(self, mock_logger):
        """Verify that a cron job needs to have a code set."""
        response = self._call(self.no_code_cron, force=True)
        self.assertIn("does not have a code attribute", response)
        mock_logger.info.assert_called()

    @override_settings(DJANGO_CRON_LOCK_BACKEND="cron.backends.lock.file.FileLock")
    def test_file_locking_backend(self):
        """Verify if the FileLock locking backend works."""
        self._call(self.success_cron, force=True)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    @override_settings(DJANGO_CRON_LOCK_BACKEND="cron.backends.lock.database.DatabaseLock")
    def test_database_locking_backend(self):
        # TODO: to test it properly we would need to run multiple jobs at the same time
        cron_job_locks = CronJobLock.objects.all().count()
        for _ in range(3):
            self._call(self.success_cron, force=True)
        self.assertEqual(CronJobLog.objects.all().count(), 3)
        self.assertEqual(CronJobLock.objects.all().count(), cron_job_locks + 1)
        self.assertEqual(CronJobLock.objects.first().locked, False)

    @patch.object(TestSuccessCronJob, "do")
    def test_dry_run_does_not_perform_task(self, mock_do):
        response = self._call(self.success_cron, dry_run=True)
        self.assertReportedRun(TestSuccessCronJob, response)
        mock_do.assert_not_called()
        self.assertFalse(CronJobLog.objects.exists())

    @patch.object(TestSuccessCronJob, "do")
    def test_non_dry_run_performs_task(self, mock_do):
        mock_do.return_value = ["message"]
        response = self._call(self.success_cron)
        self.assertReportedRun(TestSuccessCronJob, response)
        mock_do.assert_called_once()
        self.assertEqual(1, CronJobLog.objects.count())
        log = CronJobLog.objects.get()
        self.assertEqual("message", log.message.strip())  # CronJobManager adds new line at the end of each message
        self.assertTrue(log.is_success)

    def test_runs_every_mins(self):
        current_time = timezone.now()

        with freeze_time(current_time):
            response = self._call(self.five_mins_cron)
        self.assertReportedRun(Test5minsCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time(current_time + timedelta(minutes=4, seconds=59)):
            response = self._call(self.five_mins_cron)
        self.assertReportedNoRun(Test5minsCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time(current_time + timedelta(minutes=5, seconds=1)):
            response = self._call(self.five_mins_cron)
        self.assertReportedRun(Test5minsCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

    def test_runs_every_mins_with_tolerance(self):
        with freeze_time("2014-01-01 00:00:00", tz_offset=-1):
            call_command("runcrons", self.five_mins_with_tolerance_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time("2014-01-01 00:04:59", tz_offset=-1):
            call_command("runcrons", self.five_mins_with_tolerance_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

        with freeze_time("2014-01-01 00:05:01", tz_offset=-1):
            call_command("runcrons", self.five_mins_with_tolerance_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

        with freeze_time("2014-01-01 00:09:40", tz_offset=-1):
            call_command("runcrons", self.five_mins_with_tolerance_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

        with freeze_time("2014-01-01 00:09:54", tz_offset=-1):
            call_command("runcrons", self.five_mins_with_tolerance_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

        with freeze_time("2014-01-01 00:09:55", tz_offset=-1):
            call_command("runcrons", self.five_mins_with_tolerance_cron)
        self.assertEqual(CronJobLog.objects.all().count(), 3)

    @override_settings(DJANGO_CRON_DELETE_LOGS_OLDER_THAN=1)
    def test_runs_at_time(self):
        current_time = timezone.now()

        with freeze_time(current_time.replace(hour=0, minute=0, second=1, microsecond=0)):
            response = self._call(self.run_at_times_cron)
        self.assertReportedRun(TestRunAtTimesCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time(current_time.replace(hour=0, minute=4, second=50, microsecond=0)):
            response = self._call(self.run_at_times_cron)
        self.assertReportedNoRun(TestRunAtTimesCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

        with freeze_time(current_time.replace(hour=0, minute=5, second=1, microsecond=0)):
            response = self._call(self.run_at_times_cron)
        self.assertReportedRun(TestRunAtTimesCronJob, response)
        self.assertEqual(CronJobLog.objects.all().count(), 2)

    def test_run_on_weekend(self):
        for test_date in ("2017-06-17", "2017-06-18"):  # Saturday and Sunday
            logs_count = CronJobLog.objects.all().count()
            with freeze_time(test_date):
                call_command("runcrons", self.run_on_wkend_cron)
            self.assertEqual(CronJobLog.objects.all().count(), logs_count + 1)

        for test_date in (
            "2017-06-19",
            "2017-06-20",
            "2017-06-21",
            "2017-06-22",
            "2017-06-23",
        ):  # Mon-Fri
            logs_count = CronJobLog.objects.all().count()
            with freeze_time(test_date):
                call_command("runcrons", self.run_on_wkend_cron)
            self.assertEqual(CronJobLog.objects.all().count(), logs_count)

    @override_settings(DJANGO_CRON_DELETE_LOGS_OLDER_THAN=1000)
    def test_run_on_month_days(self):
        for test_date in (
            datetime.datetime.strptime("2010-10-1", "%Y-%m-%d"),
            datetime.datetime.strptime("2010-10-10", "%Y-%m-%d"),
            datetime.datetime.strptime("2010-10-20", "%Y-%m-%d"),
        ):
            logs_count = CronJobLog.objects.all().count()
            with freeze_time(test_date):
                call_command("runcrons", self.run_on_month_days)
            self.assertEqual(CronJobLog.objects.all().count(), logs_count + 1)

        for test_date in (
            datetime.datetime.strptime("2010-10-2", "%Y-%m-%d").replace(
                tzinfo=tz.gettz(timezone.get_current_timezone_name())
            ),
            datetime.datetime.strptime("2010-10-9", "%Y-%m-%d").replace(
                tzinfo=tz.gettz(timezone.get_current_timezone_name())
            ),
            datetime.datetime.strptime("2010-10-11", "%Y-%m-%d").replace(
                tzinfo=tz.gettz(timezone.get_current_timezone_name())
            ),
            datetime.datetime.strptime("2010-10-19", "%Y-%m-%d").replace(
                tzinfo=tz.gettz(timezone.get_current_timezone_name())
            ),
            datetime.datetime.strptime("2010-10-21", "%Y-%m-%d").replace(
                tzinfo=tz.gettz(timezone.get_current_timezone_name())
            ),
        ):
            logs_count = CronJobLog.objects.all().count()
            with freeze_time(test_date):
                call_command("runcrons", self.run_on_month_days)
            self.assertEqual(CronJobLog.objects.all().count(), logs_count)

    def test_silent_produces_no_output_success(self):
        response = self._call(self.success_cron, silent=True)
        self.assertEqual(1, CronJobLog.objects.count())
        self.assertEqual("", response)

    def test_silent_produces_no_output_no_run(self):
        time_to_freeze = timezone.now()
        time_to_freeze = time_to_freeze.replace(month=1, day=1, hour=0, minute=0, second=0)
        with freeze_time(time_to_freeze):
            response = self._call(self.run_at_times_cron, silent=True)
        self.assertEqual(1, CronJobLog.objects.count())
        self.assertEqual("", response)

        time_to_freeze = time_to_freeze.replace(month=1, day=1, hour=0, minute=0, second=1)
        with freeze_time(time_to_freeze):
            response = self._call(self.run_at_times_cron, silent=True)

        self.assertEqual(1, CronJobLog.objects.count())
        self.assertEqual("", response)

    def test_silent_produces_no_output_failure(self):
        response = self._call(self.error_cron, silent=True)
        self.assertEqual("", response)

    def test_admin(self):
        password = "test"
        user = User.objects.create_superuser("test", password=password)
        self.client = Client()
        self.client.login(username=user.username, password=password)

        # edit CronJobLog object
        self._call(self.success_cron, force=True)
        log = CronJobLog.objects.all()[0]
        url = reverse("admin:cron_cronjoblog_change", args=(log.id,))
        response = self.client.get(url)
        self.assertIn("Cron job logs", str(response.content))

    def run_cronjob_in_thread(self, logs_count):
        self._call(self.wait_3sec_cron)
        self.assertEqual(CronJobLog.objects.all().count(), logs_count + 1)
        db.close_old_connections()

    def test_cache_locking_backend(self):
        t = threading.Thread(target=self.run_cronjob_in_thread, args=(0,))
        t.daemon = True
        t.start()
        # this shouldn't get running
        sleep(0.1)  # to avoid race condition
        self._call(self.wait_3sec_cron)
        t.join(10)
        self.assertEqual(CronJobLog.objects.all().count(), 1)

    def test_failed_runs_notification(self):
        CronJobLog.objects.all().delete()

        for i in range(10):
            self._call(self.error_cron, force=True)
        self._call(self.test_failed_runs_notification_cron)

        self.assertEqual(CronJobLog.objects.all().count(), 11)

    def test_humanize_duration(self):
        test_subjects = (
            (
                timedelta(days=1, hours=1, minutes=1, seconds=1),
                "1 day, 1 hour, 1 minute, 1 second",
            ),
            (timedelta(days=2), "2 days"),
            (timedelta(days=15, minutes=4), "15 days, 4 minutes"),
            (timedelta(), "< 1 second"),
        )

        for duration, humanized in test_subjects:
            self.assertEqual(humanize_duration(duration), humanized)

    def test_remove_old_succeeded_job_logs(self):
        mock_date = datetime.datetime(2022, 5, 1, 12, 0, 0, tzinfo=tz.gettz(timezone.get_current_timezone_name()))
        for _ in range(5):
            with freeze_time(mock_date):
                call_command("runcrons", self.run_and_remove_old_logs)
            self.assertEqual(CronJobLog.objects.all().count(), 1)
            self.assertEqual(CronJobLog.objects.all().first().end_time, mock_date)

    @override_settings(DJANGO_CRON_DELETE_LOGS_OLDER_THAN=1000)
    def test_run_job_with_logs_in_future(self):
        mock_date_in_future = timezone.now() + datetime.timedelta(days=365)
        with freeze_time(mock_date_in_future):
            call_command("runcrons", self.five_mins_cron)
            self.assertEqual(CronJobLog.objects.all().count(), 1)
            self.assertEqual(CronJobLog.objects.all().first().end_time, mock_date_in_future)

        mock_date_in_past = timezone.now() - datetime.timedelta(days=365)
        with freeze_time(mock_date_in_past):
            call_command("runcrons", self.five_mins_cron)
            self.assertEqual(CronJobLog.objects.all().count(), 2)
            self.assertEqual(CronJobLog.objects.all().order_by("start_time").first().end_time, mock_date_in_past)

        mock_date_in_future_plus_one_minute = mock_date_in_future + timedelta(minutes=1)
        with freeze_time(mock_date_in_future_plus_one_minute):
            call_command("runcrons", self.five_mins_cron)
            self.assertEqual(CronJobLog.objects.all().count(), 2)
            # Old job log will be removed.
            self.assertEqual(CronJobLog.objects.all().order_by("start_time").first().end_time, mock_date_in_past)


class TestCronLoop(TransactionTestCase):
    success_cron = "cron.tests.crons.TestSuccessCronJob"

    def _call(self, *args, **kwargs):
        return call("cronloop", *args, **kwargs)

    def test_repeat_twice(self):
        self._call(cron_classes=[self.success_cron, self.success_cron], repeat=2, sleep=1)
        self.assertEqual(CronJobLog.objects.all().count(), 4)
