from django.urls import path

from fridges.api.v1.views import FridgeUnlockAPIView

urlpatterns = [
    path("unlock/", FridgeUnlockAPIView.as_view(), name="fridge_unlock"),
]
