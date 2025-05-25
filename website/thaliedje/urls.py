from django.urls import path, register_converter

from thaliedje import views
from .converters import PlayerConverter


register_converter(PlayerConverter, "player")

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("player/<player:player>/", views.NowPlayingView.as_view(), name="now_playing"),
    path(
        "event-control/create/<int:pk>/",
        views.ThaliedjeControlEventCreateView.as_view(),
        name="create-control-event",
    ),
    path(
        "event-control/<int:pk>/",
        views.ThaliedjeControlEventView.as_view(),
        name="event-control",
    ),
    path(
        "event-control/<int:pk>/join/<str:code>/",
        views.ThaliedjeControlEventJoinView.as_view(),
        name="join-event",
    ),
]
