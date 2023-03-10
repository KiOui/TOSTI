from django.urls import path, register_converter

from orders.api.v1.views import (
    ShiftListCreateAPIView,
    ShiftScannerAPIView,
    OrderListCreateAPIView,
    OrderRetrieveUpdateDestroyAPIView,
    ProductListAPIView,
    ShiftRetrieveUpdateAPIView,
    OrderVenueListAPIView,
)
from orders.converters import ShiftConverter, OrderConverter

register_converter(ShiftConverter, "shift")
register_converter(OrderConverter, "order")

urlpatterns = [
    path("shifts/", ShiftListCreateAPIView.as_view(), name="shifts_listcreate"),
    path("shifts/<int:pk>/", ShiftRetrieveUpdateAPIView.as_view(), name="shift_retrieveupdate"),
    path("shifts/<shift:shift>/orders/", OrderListCreateAPIView.as_view(), name="orders_listcreate"),
    path(
        "shifts/<shift:shift>/orders/<int:pk>/",
        OrderRetrieveUpdateDestroyAPIView.as_view(),
        name="orders_retrieveupdatedestroy",
    ),
    path("shifts/<shift:shift>/scanner/", ShiftScannerAPIView.as_view(), name="shifts_scanner"),
    path("shifts/<shift:shift>/products/", ProductListAPIView.as_view(), name="product_list"),
    path("order-venues/", OrderVenueListAPIView.as_view(), name="ordervenues_list"),
]
