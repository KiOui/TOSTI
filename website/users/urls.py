from django.urls import path
from .views import AccountFilterView, StaffView

urlpatterns = [
    path("account/", AccountFilterView.as_view(), name="account"),
    path("staff/", StaffView.as_view(), name="staff"),
]
