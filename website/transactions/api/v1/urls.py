from django.urls import path
from transactions.api.v1.views import AccountRetrieveAPIView

urlpatterns = [
    path("account/", AccountRetrieveAPIView.as_view(), name="account_retrieve"),
]
