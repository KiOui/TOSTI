from django.urls import path, register_converter
from .views import (
    IndexView,
    NowPlayingView,
    PlayerRefreshView,
    QueueRefreshView,
    search_view,
    add_view,
    next_view,
    previous_view,
    play_view,
    pause_view,
)
from .converters import SpotifyAccountConverter
from venues.converters import VenueConverter


register_converter(VenueConverter, "venue")
register_converter(SpotifyAccountConverter, "spotify")

urlpatterns = [
    path("index", IndexView.as_view(), name="index"),
    path("player/<venue:venue>", NowPlayingView.as_view(), name="now_playing"),
    path(
        "player/<spotify:spotify>/refresh",
        PlayerRefreshView.as_view(),
        name="player_refresh",
    ),
    path(
        "player/<spotify:spotify>/queue/refresh",
        QueueRefreshView.as_view(),
        name="queue_refresh",
    ),
    path("player/<spotify:spotify>/search", search_view, name="player_search"),
    path("player/<spotify:spotify>/add", add_view, name="player_add"),
    path("player/<spotify:spotify>/play", play_view, name="player_play"),
    path("player/<spotify:spotify>/pause", pause_view, name="player_pause"),
    path("player/<spotify:spotify>/next", next_view, name="player_next"),
    path("player/<spotify:spotify>/previous", previous_view, name="player_previous"),
]
