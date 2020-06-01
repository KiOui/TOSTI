from django.urls.converters import IntConverter
from .models import Venue


class VenueConverter(IntConverter):
    """Converter for Venue model."""

    def to_python(self, value):
        """
        Cast integer to Venue.

        :param value: the public key of the Venue
        :return: a Venue or ValueError
        """
        try:
            return Venue.objects.get(id=int(value))
        except Venue.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Venue to a string.

        :param obj: the Venue object
        :return: the public key of the Venue object in string format
        """
        return str(obj.pk)
