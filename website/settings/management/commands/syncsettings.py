from django.core.management import BaseCommand

from settings import models
from settings.settings import settings


class Command(BaseCommand):
    """Settings register command to synchronize all settings with the database."""

    def add_arguments(self, parser):
        """Arguments for the command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of removing and creating settings",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        print("Synchronizing settings...")
        for setting in settings.settings.keys():
            if not options["dry-run"]:
                settings.get_value(setting)
            print("Registered setting {}".format(setting))
        settings_db = models.Setting.objects.all()
        for setting in settings_db:
            if setting.slug not in settings.settings.keys():
                if not options["dry-run"]:
                    setting.delete()
                print("Deleted setting {}".format(setting))
