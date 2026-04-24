from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    """The default app config for the transactions app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "transactions"

    def ready(self):
        """Register signals."""
        from transactions import signals  # noqa

    def user_account_tabs(self, _):
        """Register user account tabs."""
        from transactions.views import (
            TransactionHistoryTabView,
        )

        return [
            {
                "name": "Transactions",
                "slug": "transactions",
                "view": TransactionHistoryTabView.as_view(),
                "order": 2,
            }
        ]
