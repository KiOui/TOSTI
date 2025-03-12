from __future__ import print_function
import traceback
from datetime import timedelta
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from cron.core import CronJobManager, get_class, BadCronJobError
from cron.models import CronJobLog


logger = logging.getLogger("cron")


DEFAULT_LOCK_TIME = 24 * 60 * 60  # 24 hours


class Command(BaseCommand):
    """Command to run cron jobs."""

    def add_arguments(self, parser):
        """
        Add arguments to the command.

        - `cron_classes`: The cron classes to run.
        - `force`: Force run crons even if not scheduled.
        - `silent`: Disable output.
        - `dry-run`: Do not actually run the cron jobs.
        """
        parser.add_argument("cron_classes", nargs="*")
        parser.add_argument("--force", action="store_true", help="Force cron runs")
        parser.add_argument("--silent", action="store_true", help="Do not push any message on console")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Just show what crons would be run; don't actually run them",
        )

    def handle(self, *args, **options):
        """Iterates over all the CRON_CLASSES (or if passed in as a commandline argument) and runs them."""
        if not options["silent"]:
            self.stdout.write("Running Crons\n")
            self.stdout.write("{0}\n".format("=" * 40))

        cron_classes = options["cron_classes"]
        if cron_classes:
            cron_class_names = cron_classes
        else:
            cron_class_names = getattr(settings, "CRON_CLASSES", [])

        try:
            crons_to_run = [get_class(x) for x in cron_class_names]
        except ImportError:
            error = traceback.format_exc()
            self.stdout.write(
                "ERROR: Make sure these are valid cron class names: %s\n\n%s" % (cron_class_names, error)
            )
            return

        for cron_class in crons_to_run:
            run_cron_with_cache_check(
                cron_class,
                force=options["force"],
                silent=options["silent"],
                dry_run=options["dry_run"],
                stdout=self.stdout,
            )

        clear_old_log_entries()
        close_old_connections()


def run_cron_with_cache_check(cron_class, force=False, silent=False, dry_run=False, stdout=None):
    """
    Checks the cache and runs the cron or not.

    :param cron_class: cron class to run.
    :param force: run jobs even if not scheduled.
    :param silent: suppress notifications.
    :param dry_run: don't actually perform the cron job.
    :param stdout: where to write feedback to.
    """
    try:
        manager = CronJobManager(cron_class, silent=silent, dry_run=dry_run, stdout=stdout)
    except BadCronJobError as e:
        if not silent:
            stdout.write(f"{e}\n")
            logger.info(e)
        return

    with manager:
        manager.run(force)


def clear_old_log_entries():
    """Removes older log entries, if the appropriate setting has been set."""
    if hasattr(settings, "DJANGO_CRON_DELETE_LOGS_OLDER_THAN"):
        delta = timedelta(days=settings.DJANGO_CRON_DELETE_LOGS_OLDER_THAN)
        CronJobLog.objects.filter(end_time__lt=timezone.now() - delta).delete()
