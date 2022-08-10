from django.urls import path

from .views import MeRetrieveAPIView

urlpatterns = [
    path("me/", MeRetrieveAPIView.as_view(), name="me"),
]
