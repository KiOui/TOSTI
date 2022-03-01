from django.urls import path, register_converter

from borrel import views
from venues.converters import VenueConverter

register_converter(VenueConverter, "venue")


urlpatterns = [
    path("reservations/", views.ListReservationsView.as_view(), name="list_reservations"),
    path("add-reservation/", views.ReservationRequestCreateView.as_view(), name="add_reservation"),
    path("reservations/<int:pk>/", views.ReservationRequestUpdateView.as_view(), name="view_reservation"),
    path("reservations/<int:pk>/submit", views.ReservationRequestSubmitView.as_view(), name="submit_reservation"),
]
