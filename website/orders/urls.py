from django.urls import path, register_converter
from .views import ShiftView, OrderView, ShiftStartView, ShiftAdminView, ShiftStatusView, OrderUpdateView
from .converters import ShiftConverter

register_converter(ShiftConverter, "shift")


urlpatterns = [
    path("shifts", ShiftView.as_view(), name="shifts"),
    path("<shift:shift>/order", OrderView.as_view(), name="order"),
    path("shifts/start", ShiftStartView.as_view(), name="shift_start"),
    path("<shift:shift>/admin", ShiftAdminView.as_view(), name="shift_admin"),
    path("<shift:shift>/status", ShiftStatusView.as_view(), name="shift_status"),
    path("update", OrderUpdateView.as_view(), name="order_update")
]
