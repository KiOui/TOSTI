from django.urls import path, register_converter
from venues.api.v1.views import (
    VenueListAPIView,
    VenueRetrieveAPIView,
    ReservationListCreateAPIView,
)
from venues.converters import VenuePkConverter

register_converter(VenuePkConverter, "venuepk")

urlpatterns = [
    path("", VenueListAPIView.as_view(), name="venue_list"),
    path("<int:pk>/", VenueRetrieveAPIView.as_view(), name="venue_retrieve"),
    path(
        "reservations/",
        ReservationListCreateAPIView.as_view(),
        name="reservations_listcreate",
    ),
]
