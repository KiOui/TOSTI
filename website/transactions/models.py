import uuid

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, IntegrityError
from django.utils import timezone

User = get_user_model()


class Account(models.Model):
    """Financial account of a user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance(self):
        """Return the balance of the account."""
        last_transaction = self.transactions.last()
        if last_transaction:
            return last_transaction._balance_after
        return 0

    def __str__(self):
        """Return the string representation of the account."""
        return str(self.user)

    class Meta:
        """Meta options for the account model."""

        verbose_name = "account"
        verbose_name_plural = "accounts"
        ordering = ["created_at"]
        get_latest_by = "created_at"


class Transaction(models.Model):
    """Transaction of an account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=False, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    description = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=255)
    processor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False, related_name="transactions_processed"
    )

    payable_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    payable_object_id = models.PositiveIntegerField(null=True, blank=True)
    payable_object = GenericForeignKey("payable_content_type", "payable_object_id")

    # The following fields are used to link transactions together and maintain the integrity of the account
    # The fields are not editable because they should be calculated automatically. This is verified in the save method.
    _balance_after = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    _previous_transaction = models.OneToOneField(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="_next_transaction", editable=False
    )

    def save(self, *args, **kwargs):
        """Save the transaction maintaining integrity of the account history."""
        # Calculate what the values of balance_after and previous_transaction should be
        self.timestamp = self.timestamp or timezone.now()
        previous_transaction = self.account.transactions.filter(timestamp__lt=self.timestamp).last()
        if previous_transaction:
            balance_after = previous_transaction._balance_after + self.amount
        else:
            balance_after = None

        # We could simply always overwrite the values of balance_after and previous_transaction
        # However, we want to make sure that the values are correct and throw an error if they are not consistent
        if self._balance_after and balance_after and self._balance_after != balance_after:
            # Check if balance after is correct, if it was already provided
            raise IntegrityError("Balance after is not equal to previous balance after + amount")
        else:
            # Calculate balance after, if it was not provided
            self._balance_after = balance_after or self.amount

        if self._previous_transaction and self._previous_transaction != previous_transaction:
            # Check if previous transaction is correct, if it was already provided
            raise IntegrityError("Previous transaction is not the last transaction of the account")
        else:
            # Set previous transaction to the last transaction of the account, if it was not provided
            self._previous_transaction = previous_transaction

        super().save(*args, **kwargs)

    def __str__(self):
        """Return the string representation of the transaction."""
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} - €{self.amount} - {self.description} ({self.account})"

    @property
    def next_transaction(self):
        """Return the next transaction of the account."""
        try:
            return self._next_transaction
        except Transaction.DoesNotExist:
            return None

    @property
    def previous_transaction(self):
        """Return the previous transaction of the account."""
        try:
            return self._previous_transaction
        except Transaction.DoesNotExist:
            return None

    def delete(self, *args, **kwargs):
        """Delete a transaction and also delete all previous transactions as well, to maintain consistency."""
        if self.next_transaction and self.previous_transaction:
            super().delete(*args, **kwargs)
            self.previous_transaction.delete()
        else:
            super().delete(*args, **kwargs)

    class Meta:
        """Meta options for the transaction model."""

        verbose_name = "transaction"
        verbose_name_plural = "transactions"
        ordering = ["timestamp"]
        get_latest_by = "timestamp"