from django.urls import path, register_converter
from .views import (
    IndexView,
    NowPlayingView,
    SpofityAuthorizeView,
    SpotifyTokenView,
    SpotifyAuthorizeSucceededView,
    PlayerRefreshView,
    QueueRefreshView,
    search_view,
    add_view,
    next_view,
    previous_view,
    play_view,
    pause_view,
)
from .converters import SpotifyAuthCodeConverter
from venues.converters import VenueConverter


register_converter(VenueConverter, "venue")
register_converter(SpotifyAuthCodeConverter, "auth")

urlpatterns = [
    path("index", IndexView.as_view(), name="index"),
    path("player/<venue:venue>", NowPlayingView.as_view(), name="now_playing"),
    path("admin/authorize", SpofityAuthorizeView.as_view(), name="authorize"),
    path("admin/token", SpotifyTokenView.as_view(), name="add_token"),
    path(
        "admin/succeeded/<auth:auth>",
        SpotifyAuthorizeSucceededView.as_view(),
        name="authorization_succeeded",
    ),
    path(
        "player/<auth:auth>/refresh", PlayerRefreshView.as_view(), name="player_refresh"
    ),
    path(
        "player/<auth:auth>/queue/refresh",
        QueueRefreshView.as_view(),
        name="queue_refresh",
    ),
    path("player/<auth:auth>/search", search_view, name="player_search"),
    path("player/<auth:auth>/add", add_view, name="player_add"),
    path("player/<auth:auth>/play", play_view, name="player_play"),
    path("player/<auth:auth>/pause", pause_view, name="player_pause"),
    path("player/<auth:auth>/next", next_view, name="player_next"),
    path("player/<auth:auth>/previous", previous_view, name="player_previous"),
]
