from django.urls import path

from .views import MeRetrieveAPIView, IdentificationTokenView

urlpatterns = [
    path("me/", MeRetrieveAPIView.as_view(), name="me"),
    path("id-token/", IdentificationTokenView.as_view(), name="id-token"),
]
