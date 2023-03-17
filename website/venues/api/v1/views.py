import django_filters.rest_framework
from rest_framework import permissions
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView, ListCreateAPIView
from tosti.api.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from tosti.api.v1.pagination import StandardResultsSetPagination

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
    filterset_class = VenueFilter
    search_fields = ["name", "slug"]


class VenueRetrieveAPIView(RetrieveAPIView):
    """
    Venue Retrieve API View.

    Permissions required: None

    Use this endpoint to get the details of a Venue.
    """

    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(active=True)


class ReservationListCreateAPIView(ListCreateAPIView):
    """
    Reservation List Create API View.

    Permissions required: None for GET, write for POST

    Use this endpoint to get the Reservations of a Venue or create a Reservation.
    """

    serializer_class = ReservationSerializer
    queryset = Reservation.objects.all().select_related(
        "venue", "user_created", "user_created__association", "association"
    )
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend, SearchFilter)
    filterset_class = ReservationFilter
    search_fields = ["title"]
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes = ["write"]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        """Add user to save."""
        return serializer.save(user_created=self.request.user)

    def check_permissions(self, request):
        """Always allow GET requests."""
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return super(ReservationListCreateAPIView, self).check_permissions(request)
