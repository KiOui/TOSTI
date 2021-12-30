from django.urls import path

from venues import views

urlpatterns = [
    path("calendar/", views.VenueCalendarView.as_view(), name="calendar"),
    path("calendar/add-reservation/", views.RequestReservationView.as_view(), name="add_reservation"),
]
