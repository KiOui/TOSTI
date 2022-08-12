from django.urls import path

from status_screen import views

urlpatterns = [
    path("<venue:venue>/", views.StatusScreenView.as_view(), name="status_screen"),
]
