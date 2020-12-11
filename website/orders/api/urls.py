from django.urls import path, register_converter, include
from rest_framework.routers import DefaultRouter

from orders.api.viewsets.orders import (
    OrderView,
    OrderViewSet,
    ShiftViewSet,
    shift_add_time,
    shift_add_capacity,
    shift_scanner,
    ProductViewSet,
)
from orders.converters import OrderConverter, ShiftConverter

router = DefaultRouter()
router.register(r"shifts", ShiftViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"products", ProductViewSet)

register_converter(OrderConverter, "order")
register_converter(ShiftConverter, "shift")

urlpatterns = [
    path("", include(router.urls)),
    path("shift/<shift:shift>/add-time/", shift_add_time, name="shift_add_time"),
    path("shift/<shift:shift>/add-capacity/", shift_add_capacity, name="shift_add_capacity"),
    path("shift/<shift:shift>/scanner/", shift_scanner, name="shift_scanner"),
    path("shift/<shift:shift>/order", OrderView.as_view(), name="order"),
]
