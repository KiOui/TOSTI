from django.urls.converters import IntConverter, SlugConverter

from venues.models import Venue
from .models import Shift, Order, OrderVenue


class ShiftConverter(IntConverter):
    """Converter for Project model."""

    def to_python(self, value):
        """
        Cast integer to Project.

        :param value: the public key of the Project
        :return: a Project or ValueError
        """
        try:
            return Shift.objects.get(pk=int(value))
        except Shift.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Project to a string.

        :param obj: the Project object
        :return: the public key of the Project object in string format
        """
        return str(obj.pk)


class OrderVenueConverter(SlugConverter):
    """Converter for OrderVenue model."""

    def to_python(self, value):
        """
        Cast slug to OrderVenue.

        :param value: the slug of the Venue
        :return: a OrderVenue or ValueError
        """
        try:
            return OrderVenue.objects.get(venue=Venue.objects.get(slug=value))
        except OrderVenue.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of OrderVenue to a string.

        :param obj: the OrderVenue object
        :return: the slug of the OrderVenue object
        """
        return obj.venue.slug


class OrderConverter(IntConverter):
    """Converter for Venue model."""

    def to_python(self, value):
        """
        Cast integer to Order.

        :param value: the public key of the Order
        :return: a Order or ValueError
        """
        try:
            return Order.objects.get(pk=int(value))
        except Order.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        """
        Cast an object of Order to a string.

        :param obj: the Order object
        :return: the public key of the Order object in string format
        """
        return str(obj.pk)
