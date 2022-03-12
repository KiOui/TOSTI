from django.urls import path, register_converter

from borrel import views
from venues.converters import VenueConverter

register_converter(VenueConverter, "venue")


urlpatterns = [
    path("reservations/", views.ListReservationsView.as_view(), name="list_reservations"),
    path("add-reservation/", views.BorrelReservationCreateView.as_view(), name="add_reservation"),
    path("reservations/<int:pk>/", views.BorrelBorrelReservationUpdateView.as_view(), name="view_reservation"),
    path("reservations/<int:pk>/submit/", views.BorrelReservationSubmitView.as_view(), name="submit_reservation"),
    path("reservations/<int:pk>/delete/", views.ReservationRequestCancelView.as_view(), name="delete_reservation"),
    path("reservations/join/<uuid:code>", views.JoinReservationView.as_view(), name="join_reservation"),
]
