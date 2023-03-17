from django.urls import path
from .views import AccountView, StaffView

urlpatterns = [
    path("account/", AccountView.as_view(), name="account"),
    path("staff/", StaffView.as_view(), name="staff"),
]
