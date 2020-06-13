from django.urls import path, register_converter
from .views import (
    ShiftView,
    OrderView,
    ShiftAdminView,
    OrderUpdateView,
    CreateShiftView,
    ProductListView,
    ShiftOverview,
    ToggleShiftActivationView,
    AddShiftCapacityView,
    AddShiftTimeView,
    JoinShiftView,
    RefreshHeaderView,
    RefreshAdminFooterView,
    RefreshShiftOrderView,
    RefreshProductOverviewView,
)
from .converters import ShiftConverter, VenueConverter

register_converter(ShiftConverter, "shift")
register_converter(VenueConverter, "venue")


urlpatterns = [
    path("shifts", ShiftView.as_view(), name="shifts"),
    path("<shift:shift>/order", OrderView.as_view(), name="order"),
    path("shifts/<venue:venue>/create", CreateShiftView.as_view(), name="shift_create"),
    path("<shift:shift>/admin", ShiftAdminView.as_view(), name="shift_admin"),
    path("update", OrderUpdateView.as_view(), name="order_update"),
    path("<shift:shift>/products", ProductListView.as_view(), name="product_list"),
    path("<shift:shift>/overview", ShiftOverview.as_view(), name="shift_overview"),
    path(
        "<shift:shift>/toggle", ToggleShiftActivationView.as_view(), name="shift_toggle"
    ),
    path("<shift:shift>/add-time", AddShiftTimeView.as_view(), name="shift_add_time"),
    path(
        "<shift:shift>/add-capacity",
        AddShiftCapacityView.as_view(),
        name="shift_add_capacity",
    ),
    path("<shift:shift>/join", JoinShiftView.as_view(), name="shift_join"),
    path(
        "<shift:shift>/refresh/header",
        RefreshHeaderView.as_view(),
        name="shift_refresh_header",
    ),
    path(
        "<shift:shift>/refresh/footer",
        RefreshAdminFooterView.as_view(),
        name="shift_refresh_admin_footer",
    ),
    path(
        "<shift:shift>/refresh/overview",
        RefreshProductOverviewView.as_view(),
        name="shift_refresh_product_overview",
    ),
    path(
        "<shift:shift>/refresh/orders",
        RefreshShiftOrderView.as_view(),
        name="shift_refresh_orders",
    ),
]
