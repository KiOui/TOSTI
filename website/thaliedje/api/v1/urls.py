from django.urls import path, register_converter
from thaliedje.api.v1.views import (
    PlayerListAPIView,
    PlayerRetrieveAPIView,
    PlayerQueueListAPIView,
    PlayerTrackSearchAPIView,
    PlayerTrackAddAPIView,
    PlayerNextAPIView,
    PlayerPreviousAPIView,
    PlayerPlayAPIView,
    PlayerPauseAPIView,
    PlayerVolumeAPIView,
)
from thaliedje.converters import PlayerConverter

register_converter(PlayerConverter, "player")

urlpatterns = [
    path("players/", PlayerListAPIView.as_view(), name="player_list"),
    path("players/<int:pk>/", PlayerRetrieveAPIView.as_view(), name="player_retrieve"),
    path("players/<player:player>/queue/", PlayerQueueListAPIView.as_view(), name="player_queue"),
    path("players/<player:player>/search/", PlayerTrackSearchAPIView.as_view(), name="player_search"),
    path("players/<player:player>/add/", PlayerTrackAddAPIView.as_view(), name="player_add"),
    path("players/<player:player>/play/", PlayerPlayAPIView.as_view(), name="player_play"),
    path("players/<player:player>/pause/", PlayerPauseAPIView.as_view(), name="player_pause"),
    path("players/<player:player>/next/", PlayerNextAPIView.as_view(), name="player_next"),
    path("players/<player:player>/previous/", PlayerPreviousAPIView.as_view(), name="player_previous"),
    path("players/<player:player>/volume/", PlayerVolumeAPIView.as_view(), name="player_volume"),
]
