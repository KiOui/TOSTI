from django.urls import path, register_converter

from venues import views
from venues.converters import VenueConverter

register_converter(VenueConverter, "venue")


urlpatterns = [
    path("calendar/", views.VenueCalendarView.as_view(), name="calendar"),
    path("reservations/", views.ListReservationsView.as_view(), name="list_reservations"),
    path("add-reservation/", views.RequestReservationView.as_view(), name="add_reservation"),
    path("reservations.ics", views.ReservationFeed(), name="ical_reservations"),
    path("reservations-<venue:venue>.ics", views.ReservationVenueFeed(), name="ical_venue_reservations"),
]
