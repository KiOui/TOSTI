from django.urls import path, register_converter
from venues.api.v1.views import (
    VenueListAPIView,
    VenueRetrieveAPIView,
    ReservationListAPIView,
    VenueReservationListAPIView,
)
from venues.converters import VenuePkConverter

register_converter(VenuePkConverter, "venue")

urlpatterns = [
    path("", VenueListAPIView.as_view(), name="venue_list"),
    path("<int:pk>", VenueRetrieveAPIView.as_view(), name="venue_retrieve"),
    path("reservations", ReservationListAPIView.as_view(), name="reservations_list"),
    path("<venue:venue>/reservations", VenueReservationListAPIView.as_view(), name="venue_reservations_list"),
]
