from django.urls import path, register_converter

from thaliedje import views
from .converters import SpotifyAccountConverter
from venues.converters import VenueConverter


register_converter(VenueConverter, "venue")
register_converter(SpotifyAccountConverter, "player")

urlpatterns = [
    path("index", views.IndexView.as_view(), name="index"),
    path("player/<venue:venue>", views.NowPlayingView.as_view(), name="now_playing"),
    path(
        "player/<player:player>/refresh",
        views.PlayerRefreshView.as_view(),
        name="player_refresh",
    ),
    path(
        "player/<player:player>/queue/refresh",
        views.QueueRefreshView.as_view(),
        name="queue_refresh",
    ),
    path("player/<player:player>/search", views.search_view, name="player_search"),
    path("player/<player:player>/add", views.add_view, name="player_add"),
    path("player/<player:player>/play", views.play_view, name="player_play"),
    path("player/<player:player>/pause", views.pause_view, name="player_pause"),
    path("player/<player:player>/next", views.next_view, name="player_next"),
    path(
        "player/<player:player>/previous", views.previous_view, name="player_previous"
    ),
]
