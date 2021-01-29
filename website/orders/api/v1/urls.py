from django.urls import path, register_converter

from orders.api.v1.views import (
    CartOrderAPIView,
    ShiftListCreateAPIView,
    shift_add_time,
    shift_add_capacity,
    shift_scanner,
    OrderListCreateAPIView,
    OrderRetrieveDestroyAPIView,
    ProductListAPIView,
    ShiftRetrieveUpdateAPIView,
    product_search,
    order_toggle_paid,
    order_toggle_ready,
)
from orders.converters import ShiftConverter, OrderConverter

register_converter(ShiftConverter, "shift")
register_converter(OrderConverter, "order")

urlpatterns = [
    path("shifts", ShiftListCreateAPIView.as_view(), name="shifts_listcreate"),
    path("shifts/<int:pk>", ShiftRetrieveUpdateAPIView.as_view(), name="shift_retrieveupdate"),
    path("shifts/<shift:shift>/orders", OrderListCreateAPIView.as_view(), name="orders_listcreate"),
    path(
        "shifts/<shift:shift>/orders/<int:pk>", OrderRetrieveDestroyAPIView.as_view(), name="orders_retrievedestroy",
    ),
    path("shifts/<shift:shift>/orders/<order:order>/paid", order_toggle_paid, name="order_toggle_paid"),
    path("shifts/<shift:shift>/orders/<order:order>/ready", order_toggle_ready, name="order_toggle_ready"),
    path("shifts/<shift:shift>/add-time", shift_add_time, name="shifts_add_time"),
    path("shifts/<shift:shift>/add-capacity", shift_add_capacity, name="shifts_add_capacity"),
    path("shifts/<shift:shift>/scanner", shift_scanner, name="shifts_scanner"),
    path("shifts/<shift:shift>/cart-order", CartOrderAPIView.as_view(), name="shifts_cart_order"),
    path("shifts/<shift:shift>/products", ProductListAPIView.as_view(), name="product_list"),
    path("shifts/<shift:shift>/search", product_search, name="product_search"),
]
