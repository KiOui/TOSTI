from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    """The default app config for the transactions app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "transactions"

    def ready(self):
        """
        Ready method.

        :return: None
        """
        from users.views import AccountFilterView
        from transactions.views import (
            TransactionHistoryTabView,
        )

        def filter_user_page(user_page_list: list):
            """Add transactions tab on accounts page."""
            user_page_list.append(
                {
                    "name": "Transactions",
                    "slug": "transactions",
                    "view": TransactionHistoryTabView.as_view(),
                }  # noqa
            )
            return user_page_list

        AccountFilterView.user_data_tabs.add_filter(filter_user_page, 2)
