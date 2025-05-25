from django.urls import path
from transactions.api.v1.views import AccountRetrieveAPIView, TransactionCreateAPIView

urlpatterns = [
    path("", TransactionCreateAPIView.as_view(), name="transaction_create"),
    path(
        "retrieve-account/", AccountRetrieveAPIView.as_view(), name="account_retrieve"
    ),
]
