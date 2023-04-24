from django.core.management import BaseCommand

from tosti.filter import Filter


class Command(BaseCommand):
    """Command to create random fixtures."""

    fixture_creators = Filter()

    def handle(self, *args, **kwargs):
        """Create random fixtures, in order of filters."""
        creators_list = self.fixture_creators.do_filter([])
        for creator in creators_list:
            print("Running {}".format(creator))
            creator()
