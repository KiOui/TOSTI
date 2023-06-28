from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase

from transactions.models import Account

User = get_user_model()


class TransactionModelTestCase(TestCase):
    """Test the transaction model."""

    def setUp(self):
        """Set up the test case."""
        self.user = User.objects.create_user(username="test", password="test")
        self.account = Account.objects.create(user=self.user)

    def test_create_transaction(self):
        """Test creating a chain of transactions."""
        # Create a first transaction
        t1 = self.account.transactions.create(amount=10, description="test", processor=self.user)
        self.assertEqual(self.account.transactions.last(), t1)
        self.assertEqual(self.account.balance, 10)
        self.assertEqual(self.account.transactions.count(), 1)
        self.assertEqual(t1._balance_after, 10)
        self.assertEqual(t1._previous_transaction, None)

        # Create a second transaction, this should link to the first one
        t2 = self.account.transactions.create(amount=5, description="test", processor=self.user)
        self.account.refresh_from_db()

        self.assertEqual(self.account.transactions.last(), t2)
        self.assertEqual(self.account.balance, 15)
        self.assertEqual(self.account.transactions.count(), 2)
        self.assertEqual(t2._balance_after, 15)
        self.assertEqual(t2._previous_transaction, t1)

        # Create a third transaction, this should link to the second one
        t3 = self.account.transactions.create(amount=7, description="test", processor=self.user)
        self.account.refresh_from_db()

        self.assertEqual(self.account.transactions.last(), t3)
        self.assertEqual(self.account.balance, 22)
        self.assertEqual(self.account.transactions.count(), 3)
        self.assertEqual(t3._balance_after, 22)
        self.assertEqual(t3._previous_transaction, t2)

        self.assertEqual(self.account.transactions.first(), t1)
        self.assertEqual(self.account.transactions.last(), t3)

        # Delete deleting an old transaction that another transaction is built upon should fail
        with self.assertRaises(ProtectedError):
            t1.delete()

        # But if we force-delete it, it should work, but the balance should still be unaffected
        self.account.transactions.filter(pk=t2.pk).update(_previous_transaction=None)
        t1.delete()
        self.account.refresh_from_db()
        t2.refresh_from_db()

        self.assertEqual(self.account.balance, 22)
        self.assertEqual(self.account.transactions.count(), 2)
        self.assertEqual(t2._previous_transaction, None)
        self.assertEqual(t2._balance_after, 15)
        self.assertEqual(self.account.transactions.first(), t2)
        self.assertEqual(self.account.transactions.last(), t3)

        # Now create yet another transaction, this should link to the last one
        t4 = self.account.transactions.create(amount=2, description="test", processor=self.user)
        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, 24)
        self.assertEqual(self.account.transactions.count(), 3)
        self.assertEqual(t4._balance_after, 24)
        self.assertEqual(t4._previous_transaction, t3)

        # Delete the transaction at the end, this should be possible, and affect the balance
        t4.delete()
        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, 22)
        self.assertEqual(self.account.transactions.count(), 2)

        t5 = self.account.transactions.create(amount=9, description="test", processor=self.user)
        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, 31)
        self.assertEqual(self.account.transactions.count(), 3)
        self.assertEqual(t5._balance_after, 31)
        self.assertEqual(t5._previous_transaction, t3)

        # Delete the transaction in the middle, this shouldn't be possible
        with self.assertRaises(ProtectedError):
            t3.delete()

        # But if it were to be force-deleted, it should work, but the balance should still be unaffected
        self.account.transactions.filter(pk=t5.pk).update(_previous_transaction=None)
        t3.delete()
        self.account.refresh_from_db()
        t5.refresh_from_db()

        self.assertEqual(self.account.balance, 31)
        self.assertEqual(
            self.account.transactions.count(), 2
        )  # t2 still exists, but t3 is gone, so there are only 2 transactions left
        # Note that our history is now broken, but the balance is still correct
        self.assertEqual(self.account.transactions.first(), t2)
        self.assertEqual(self.account.transactions.last(), t5)
        self.assertEqual(t5._previous_transaction, None)
        self.assertEqual(t5._balance_after, 31)
        t5.save()

    def test_create_invalid_history_transaction(self):
        """Test creating a transaction with an invalid history."""
        t1 = self.account.transactions.create(amount=10, description="test", processor=self.user)
        self.account.transactions.create(amount=5, description="test", processor=self.user)

        with self.assertRaises(IntegrityError):
            self.account.transactions.create(
                amount=7, description="test", processor=self.user, _previous_transaction=t1
            )

    def test_create_invalid_balance_transaction(self):
        """Test creating a transaction with an invalid balance."""
        self.account.transactions.create(amount=10, description="test", processor=self.user)
        self.account.transactions.create(amount=5, description="test", processor=self.user)

        with self.assertRaises(IntegrityError):
            self.account.transactions.create(amount=7, description="test", processor=self.user, _balance_after=20)

    def test_alter_transaction(self):
        """Test altering a transaction."""
        t1 = self.account.transactions.create(amount=10, description="test", processor=self.user)
        t1.amount = 7
        with self.assertRaises(IntegrityError):
            t1.save()
