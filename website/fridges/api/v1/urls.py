from django.urls import path, register_converter

from fridges.api.v1.views import FridgeUnlockAPIView
from fridges.converters import FridgeConverter

register_converter(FridgeConverter, "fridge")

urlpatterns = [
    path("<fridge:fridge>/", FridgeUnlockAPIView.as_view(), name="fridge_unlock"),
]
