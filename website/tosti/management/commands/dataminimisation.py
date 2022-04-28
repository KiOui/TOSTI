import logging

from django.core.management import BaseCommand

import thaliedje.services
import orders.services
import users.services


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
        processed_orders = orders.services.execute_data_minimisation(options["dry-run"])
        for p in processed_orders:
            logger.info("Removed order data for {}".format(p))
        processed_thaliedje = thaliedje.services.execute_data_minimisation(options["dry-run"])
        for p in processed_thaliedje:
            logger.info("Removed thaliedje data for {}".format(p))
        processed_users = users.services.execute_data_minimisation(options["dry-run"])
        for p in processed_users:
            logger.info("Removed user account for {}".format(p))
