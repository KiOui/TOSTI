from django.urls import path
from .views import AccountView

urlpatterns = [
    path("account/", AccountView.as_view(), name="account"),
]
