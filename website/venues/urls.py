from django.urls import path, register_converter

from venues import views
from venues.converters import VenueConverter

register_converter(VenueConverter, "venue")


urlpatterns = [
    path("calendar/", views.VenueCalendarView.as_view(), name="calendar"),
    path(
        "reservations/", views.ListReservationsView.as_view(), name="list_reservations"
    ),
    path(
        "reservations/<int:pk>/",
        views.ReservationUpdateView.as_view(),
        name="view_reservation",
    ),
    path(
        "reservations/<int:pk>/delete/",
        views.ReservationCancelView.as_view(),
        name="delete_reservation",
    ),
    path(
        "reservations/join/<str:code>",
        views.JoinReservationView.as_view(),
        name="join_reservation",
    ),
    path(
        "add-reservation/",
        views.RequestReservationView.as_view(),
        name="add_reservation",
    ),
    path("reservations.ics", views.ReservationFeed(), name="ical_reservations"),
    path(
        "reservations-<venue:venue>.ics",
        views.ReservationVenueFeed(),
        name="ical_venue_reservations",
    ),
]
