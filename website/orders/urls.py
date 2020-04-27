from django.urls import path, register_converter
from .views import ShiftView, OrderView
from .converters import ShiftConverter

register_converter(ShiftConverter, "shift")


urlpatterns = [
    path("shifts", ShiftView.as_view(), name="shifts"),
    path("<shift:shift>/order", OrderView.as_view(), name="order")
]