import logging

from django.core.management import BaseCommand

from tosti.services import data_minimisation

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Data minimisation command to execute data minimization according to privacy policy."""

    def add_arguments(self, parser):
        """Arguments for the command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of saving data",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        data_minimisation(options["dry-run"])
