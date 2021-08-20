from django.urls import path, register_converter

from orders.api.v1.views import (
    CartOrderAPIView,
    ShiftListCreateAPIView,
    ShiftAddTimeAPIView,
    ShiftAddCapacityAPIView,
    ShiftScannerAPIView,
    OrderListCreateAPIView,
    OrderRetrieveDestroyAPIView,
    ProductListAPIView,
    ShiftRetrieveUpdateAPIView,
    ProductSearchAPIView,
    OrderTogglePaidAPIView,
    OrderToggleReadyAPIView,
    JoinShiftAPIView,
)
from orders.converters import ShiftConverter, OrderConverter

register_converter(ShiftConverter, "shift")
register_converter(OrderConverter, "order")

urlpatterns = [
    path("shifts", ShiftListCreateAPIView.as_view(), name="shifts_listcreate"),
    path("shifts/<int:pk>", ShiftRetrieveUpdateAPIView.as_view(), name="shift_retrieveupdate"),
    path("shifts/<shift:shift>/orders", OrderListCreateAPIView.as_view(), name="orders_listcreate"),
    path(
        "shifts/<shift:shift>/orders/<int:pk>",
        OrderRetrieveDestroyAPIView.as_view(),
        name="orders_retrievedestroy",
    ),
    path("shifts/<shift:shift>/orders/<order:order>/paid", OrderTogglePaidAPIView.as_view(), name="order_toggle_paid"),
    path(
        "shifts/<shift:shift>/orders/<order:order>/ready", OrderToggleReadyAPIView.as_view(), name="order_toggle_ready"
    ),
    path("shifts/<shift:shift>/add-time", ShiftAddTimeAPIView.as_view(), name="shifts_add_time"),
    path("shifts/<shift:shift>/add-capacity", ShiftAddCapacityAPIView.as_view(), name="shifts_add_capacity"),
    path("shifts/<shift:shift>/scanner", ShiftScannerAPIView.as_view(), name="shifts_scanner"),
    path("shifts/<shift:shift>/cart-order", CartOrderAPIView.as_view(), name="shifts_cart_order"),
    path("shifts/<shift:shift>/products", ProductListAPIView.as_view(), name="product_list"),
    path("shifts/<shift:shift>/search", ProductSearchAPIView.as_view(), name="product_search"),
    path("shifts/<shift:shift>/join", JoinShiftAPIView.as_view(), name="join_shift"),
]
