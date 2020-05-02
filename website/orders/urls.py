from django.urls import path, register_converter
from .views import (
    ShiftView,
    OrderView,
    ShiftAdminView,
    ShiftStatusView,
    OrderUpdateView,
    CreateShiftView,
    ProductListView,
    OrderStatusView,
)
from .converters import ShiftConverter, VenueConverter

register_converter(ShiftConverter, "shift")
register_converter(VenueConverter, "venue")


urlpatterns = [
    path("shifts", ShiftView.as_view(), name="shifts"),
    path("<shift:shift>/order", OrderView.as_view(), name="order"),
    path("shifts/<venue:venue>/create", CreateShiftView.as_view(), name="shift_create"),
    path("<shift:shift>/admin", ShiftAdminView.as_view(), name="shift_admin"),
    path("<shift:shift>/status", ShiftStatusView.as_view(), name="shift_status"),
    path("<shift:shift>/order/status", OrderStatusView.as_view(), name="order_status"),
    path("update", OrderUpdateView.as_view(), name="order_update"),
    path("<shift:shift>/products", ProductListView.as_view(), name="product_list"),
]
