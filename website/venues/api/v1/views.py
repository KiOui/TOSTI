import datetime

import pytz
from django.conf import settings
from rest_framework.generics import ListAPIView, RetrieveAPIView
from venues.models import Venue, Reservation
from .serializers import VenueSerializer, ReservationSerializer


class VenueListAPIView(ListAPIView):
    """
    Venue List API View.

    Permissions required: None

    Use this endpoint to get a list of all venues.
    """

    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(active=True)


class VenueRetrieveAPIView(RetrieveAPIView):
    """
    Venue Retrieve API View.

    Permissions required: None

    Use this endpoint to get the details of a Venue.
    """

    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(active=True)


class VenueReservationListAPIView(ListAPIView):
    """
    Venue Reservation List API View.

    Permissions required: None

    Use this endpoint to get the Reservations of a Venue.
    """

    serializer_class = ReservationSerializer
    queryset = Reservation.objects.filter(accepted=True)

    def get_queryset(self):
        """Get queryset."""
        try:
            days = int(self.request.query_params.get("days", None))
        except (TypeError, ValueError):
            days = None

        if days is not None:
            timezone = pytz.timezone(settings.TIME_ZONE)
            now = timezone.localize(datetime.datetime.now())
            return self.queryset.filter(
                venue=self.kwargs.get("venue"),
                start_time__gte=now - datetime.timedelta(days=days),
                start_time__lt=now + datetime.timedelta(days=days),
            )
        else:
            return self.queryset.filter(venue=self.kwargs.get("venue"))


class ReservationListAPIView(ListAPIView):
    """
    Reservation List API View.

    Permissions required: None

    Use this endpoint to get the Reservations of a Venue.
    """

    serializer_class = ReservationSerializer
    queryset = Reservation.objects.filter(accepted=True)

    def get_queryset(self):
        """Get queryset."""
        try:
            days = int(self.request.query_params.get("days", None))
        except (TypeError, ValueError):
            days = None

        if days is not None:
            timezone = pytz.timezone(settings.TIME_ZONE)
            now = timezone.localize(datetime.datetime.now())
            return self.queryset.filter(
                start_time__gte=now - datetime.timedelta(days=days), start_time__lt=now + datetime.timedelta(days=days)
            )
        else:
            return self.queryset
