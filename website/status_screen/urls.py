from django.urls import path

from status_screen import views

urlpatterns = [
    path("<shift:shift>/", views.StatusScreen.as_view(), name="status"),
]
