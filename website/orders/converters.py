from django.urls.converters import IntConverter

from venues.models import Venue
from .models import Shift


class ShiftConverter(IntConverter):
    """Converter for Project model."""

    def to_python(self, value):
        """
        Cast integer to Project.

        :param value: the public key of the Project
        :return: a Project or ValueError
        """
        try:
            return Shift.objects.get(id=int(value))
        except Shift.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Project to a string.

        :param obj: the Project object
        :return: the public key of the Project object in string format
        """
        return str(obj.pk)


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
