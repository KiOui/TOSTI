from django.urls import path

from venues.views import VenueCalendarView

urlpatterns = [
    path("calendar/", VenueCalendarView.as_view(), name="calendar"),
]
