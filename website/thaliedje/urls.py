from django.urls import path, register_converter

from thaliedje import views
from .converters import PlayerConverter
from venues.converters import VenueConverter


register_converter(VenueConverter, "venue")
register_converter(PlayerConverter, "player")

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("player/<venue:venue>/", views.NowPlayingView.as_view(), name="now_playing"),
]
