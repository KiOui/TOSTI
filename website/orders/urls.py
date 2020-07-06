from django.urls import path, register_converter

from orders import views
from .converters import ShiftConverter, VenueConverter, OrderConverter

register_converter(ShiftConverter, "shift")
register_converter(VenueConverter, "venue")
register_converter(OrderConverter, "order")

urlpatterns = [
    path("shifts", views.shift_view, name="shifts"),
    path("<shift:shift>/order-items", views.order_view, name="order"),
    path("venue/<venue:venue>/create", views.create_shift_view, name="shift_create"),
    path("<shift:shift>/admin", views.shift_admin_view, name="shift_admin"),
    path("order/<order:order>/update", views.order_update_view, name="order_update"),
    path("<shift:shift>/products", views.product_list_view, name="product_list"),
    path("<shift:shift>/overview", views.shift_overview_view, name="shift_overview"),
    path("<shift:shift>/control/toggle", views.toggle_shift_activation_view, name="shift_toggle"),
    path("<shift:shift>/control/add-time", views.add_shift_time_view, name="shift_add_time"),
    path("<shift:shift>/control/add-capacity", views.add_shift_capacity_view, name="shift_add_capacity"),
    path("<shift:shift>/join", views.join_shift_view, name="shift_join"),
    path("<shift:shift>/refresh/header", views.refresh_header_view, name="shift_refresh_header"),
    path("<shift:shift>/refresh/footer", views.refresh_admin_footer_view, name="shift_refresh_admin_footer"),
    path("<shift:shift>/refresh/overview", views.refresh_product_overview_view, name="shift_refresh_product_overview"),
    path("<shift:shift>/refresh/orders", views.refresh_shift_order_view, name="shift_refresh_orders"),
]
