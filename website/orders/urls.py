from django.urls import path, register_converter

from orders import views
from .converters import ShiftConverter, OrderVenueConverter, OrderConverter

register_converter(ShiftConverter, "shift")
register_converter(OrderVenueConverter, "order_venue")
register_converter(OrderConverter, "order")

urlpatterns = [
    path("venue/<order_venue:venue>/create/", views.CreateShiftView.as_view(), name="shift_create"),
    path("<shift:shift>/admin/", views.ShiftManagementView.as_view(), name="shift_admin"),
    path("<shift:shift>/overview/", views.ShiftView.as_view(), name="shift_overview"),
    path("<shift:shift>/join/", views.JoinShiftView.as_view(), name="shift_join"),
    path("<shift:shift>/status/", views.StatusScreen.as_view(), name="status"),
]
