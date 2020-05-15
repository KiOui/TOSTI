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
)
from .converters import ShiftConverter, VenueConverter
from django.contrib.admin.views.decorators import staff_member_required

register_converter(ShiftConverter, "shift")
register_converter(VenueConverter, "venue")


urlpatterns = [
    path("shifts", ShiftView.as_view(), name="shifts"),
    path("<shift:shift>/order", OrderView.as_view(), name="order"),
    path(
        "shifts/<venue:venue>/create",
        staff_member_required(CreateShiftView.as_view()),
        name="shift_create",
    ),
    path(
        "<shift:shift>/admin",
        staff_member_required(ShiftAdminView.as_view()),
        name="shift_admin",
    ),
    path(
        "update", staff_member_required(OrderUpdateView.as_view()), name="order_update"
    ),
    path("<shift:shift>/products", ProductListView.as_view(), name="product_list"),
    path("<shift:shift>/overview", ShiftOverview.as_view(), name="shift_overview"),
    path(
        "<shift:shift>/toggle",
        staff_member_required(ToggleShiftActivationView.as_view()),
        name="shift_toggle",
    ),
    path(
        "<shift:shift>/add-time",
        staff_member_required(AddShiftTimeView.as_view()),
        name="shift_add_time",
    ),
    path(
        "<shift:shift>/add-capacity",
        staff_member_required(AddShiftCapacityView.as_view()),
        name="shift_add_capacity",
    ),
    path(
        "<shift:shift>/join",
        staff_member_required(JoinShiftView.as_view()),
        name="shift_join",
    ),
    path(
        "<shift:shift>/refresh/header",
        RefreshHeaderView.as_view(),
        name="shift_refresh_header",
    ),
    path(
        "<shift:shift>/refresh/footer",
        staff_member_required(RefreshAdminFooterView.as_view()),
        name="shift_refresh_admin_footer",
    ),
    path(
        "<shift:shift>/refresh/orders",
        RefreshShiftOrderView.as_view(),
        name="shift_refresh_orders",
    ),
]
