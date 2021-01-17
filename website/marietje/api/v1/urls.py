from django.urls import path, register_converter
from marietje.api.v1.views import (
    PlayerListAPIView,
    PlayerRetrieveAPIView,
    PlayerQueueListAPIView,
    track_search,
    track_add,
    player_next,
    player_previous,
    player_play,
    player_pause,
)
from marietje.converters import PlayerConverter

register_converter(PlayerConverter, "player")

urlpatterns = [
    path("players", PlayerListAPIView.as_view(), name="player_list"),
    path("players/<int:pk>", PlayerRetrieveAPIView.as_view(), name="player_retrieve"),
    path("players/<player:player>/queue", PlayerQueueListAPIView.as_view(), name="player_queue"),
    path("players/<player:player>/search", track_search, name="player_search"),
    path("players/<player:player>/add", track_add, name="player_add"),
    path("players/<player:player>/play", player_play, name="player_play"),
    path("players/<player:player>/pause", player_pause, name="player_pause"),
    path("players/<player:player>/next", player_next, name="player_next"),
    path("players/<player:player>/previous", player_previous, name="player_previous"),
]
