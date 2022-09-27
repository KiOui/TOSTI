import django_filters.rest_framework
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView
from venues.models import Venue, Reservation
from .filters import ReservationFilter, VenueFilter
from .serializers import VenueSerializer, ReservationSerializer


class VenueListAPIView(ListAPIView):
    """
    Venue List API View.

    Permissions required: None

    Use this endpoint to get a list of all venues.
    """

    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(active=True)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, SearchFilter)
    filter_class = VenueFilter
    search_fields = ["name", "slug"]


class VenueRetrieveAPIView(RetrieveAPIView):
    """
    Venue Retrieve API View.

    Permissions required: None

    Use this endpoint to get the details of a Venue.
    """

    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(active=True)


class ReservationListAPIView(ListAPIView):
    """
    Reservation List API View.

    Permissions required: None

    Use this endpoint to get the Reservations of a Venue.
    """

    serializer_class = ReservationSerializer
    queryset = Reservation.objects.filter(accepted=True).select_related(
        "venue", "user", "user__association", "association"
    )
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, SearchFilter)
    filter_class = ReservationFilter
    search_fields = ["title"]
