from django.urls import path, register_converter

from orders import views
from .converters import ShiftConverter, VenueConverter, OrderConverter

register_converter(ShiftConverter, "shift")
register_converter(VenueConverter, "venue")
register_converter(OrderConverter, "order")

urlpatterns = [
    path("explainer/", views.ExplainerView.as_view(), name="explainer"),
    path("explainer-admin/", views.AdminExplainerView.as_view(), name="explainer_admin"),
    path("<shift:shift>/order-items/", views.PlaceOrderView.as_view(), name="order"),
    path("venue/<venue:venue>/create/", views.CreateShiftView.as_view(), name="shift_create"),
    path("<shift:shift>/admin/", views.ShiftAdminView.as_view(), name="shift_admin"),
    path("<shift:shift>/overview/", views.ShiftOverviewView.as_view(), name="shift_overview"),
    path("<shift:shift>/join/", views.JoinShiftView.as_view(), name="shift_join"),
    path("history/", views.AccountHistoryView.as_view(), name="history"),
]
