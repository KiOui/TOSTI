from django.urls import path
from .views import UserAccountTabsView, StaffView

urlpatterns = [
    path("account/", UserAccountTabsView.as_view(), name="account"),
    path("staff/", StaffView.as_view(), name="staff"),
]
