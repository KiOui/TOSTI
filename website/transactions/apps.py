from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    """The default app config for the transactions app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "transactions"
