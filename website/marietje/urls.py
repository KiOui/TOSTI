from django.urls import path, register_converter
from .views import (
    NowPlayingView,
    SpofityAuthorizeView,
    SpotifyTokenView,
    SpotifyAuthorizeSucceededView,
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
    )
]
