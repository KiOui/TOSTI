from django.urls import path

from tampon import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path(
        "notifications/",
        views.NotificationsView.as_view(),
        name="notifications",
    ),
]
