from django.urls import path, register_converter

from thaliedje import views
from .converters import PlayerConverter


register_converter(PlayerConverter, "player")

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("player/<player:player>/", views.NowPlayingView.as_view(), name="now_playing"),
]
