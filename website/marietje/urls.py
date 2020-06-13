from django.urls import path, register_converter
from .views import (
    NowPlayingView,
    SpofityAuthorizeView,
    SpotifyTokenView,
    SpotifyAuthorizeSucceededView,
    PlayerRefreshView,
    QueueRefreshView,
    search_view,
    add_view,
)
from .converters import SpotifyAuthCodeConverter
from venues.converters import VenueConverter


register_converter(VenueConverter, "venue")
register_converter(SpotifyAuthCodeConverter, "auth")

urlpatterns = [
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
]
