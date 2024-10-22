from django.urls import path

from status_screen import views

urlpatterns = [
    path("redirect/<order_venue:venue>/", views.VenueRedirectView.as_view(), name="venue-redirect"),
    path("<shift:shift>/", views.StatusScreen.as_view(), name="status"),
    path("venue/<order_venue:order_venue>", views.VenueStatusScreen.as_view(), name="venue-status")
]
