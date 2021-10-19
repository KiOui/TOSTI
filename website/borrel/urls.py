from django.urls import path, register_converter

from borrel import views
from venues.converters import VenueConverter

register_converter(VenueConverter, "venue")


urlpatterns = [
    path("calendar/", views.AllCalendarView.as_view(), name="calendars"),
    path("calendar/<venue:venue>/", views.VenueCalendarView.as_view(), name="venue_calendar"),
    path(
        "calendar/reservations/create", views.ReservationRequestCreateView.as_view(), name="reservation_request_create"
    ),
]
