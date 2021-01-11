from django.urls import path, register_converter

from orders.api.v1.views import (
    OrderView,
    ShiftListCreateAPIView,
    shift_add_time,
    shift_add_capacity,
    shift_scanner,
    OrderListAPIView,
    OrderRetrieveUpdateDestroyAPIView,
    ProductListAPIView,
    ShiftRetrieveUpdateAPIView,
    product_search,
    OrderCreateAPIView,
)
from orders.converters import ShiftConverter

register_converter(ShiftConverter, "shift")

urlpatterns = [
    path("shifts", ShiftListCreateAPIView.as_view(), name="shifts_listcreate"),
    path("shifts/<int:pk>", ShiftRetrieveUpdateAPIView.as_view(), name="shift_retrieveupdate"),
    path("shifts/<shift:shift>/orders", OrderListAPIView.as_view(), name="orders_list"),
    path(
        "shifts/<shift:shift>/orders/<int:pk>",
        OrderRetrieveUpdateDestroyAPIView.as_view(),
        name="orders_retrieveupdatedestroy",
    ),
    path("shifts/<shift:shift>/orders/add", OrderCreateAPIView.as_view(), name="orders_create"),
    path("shifts/<shift:shift>/add-time", shift_add_time, name="shifts_add_time"),
    path("shifts/<shift:shift>/add-capacity", shift_add_capacity, name="shifts_add_capacity"),
    path("shifts/<shift:shift>/scanner", shift_scanner, name="shifts_scanner"),
    path("shifts/<shift:shift>/cart-order", OrderView.as_view(), name="shifts_cart_order"),
    path("shifts/<shift:shift>/products", ProductListAPIView.as_view(), name="product_list"),
    path("shifts/<shift:shift>/search", product_search, name="product_search"),
]
