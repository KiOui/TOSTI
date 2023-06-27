from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from transactions.models import Account

User = get_user_model()


class TransactionModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="test")
        self.account = Account.objects.create(user=self.user)

    def test_create_transaction(self):
        # Create a first transaction
        t1 = self.account.transactions.create(
            amount=10, description="test", transaction_type="test", processor=self.user
        )
        self.assertEqual(self.account.transactions.last(), t1)
        self.assertEqual(self.account.balance, 10)
        self.assertEqual(self.account.transactions.count(), 1)
        self.assertEqual(t1._balance_after, 10)
        self.assertEqual(t1._previous_transaction, None)

        # Create a second transaction, this should link to the first one
        t2 = self.account.transactions.create(
            amount=5, description="test", transaction_type="test", processor=self.user
        )
        self.account.refresh_from_db()

        self.assertEqual(self.account.transactions.last(), t2)
        self.assertEqual(self.account.balance, 15)
        self.assertEqual(self.account.transactions.count(), 2)
        self.assertEqual(t2._balance_after, 15)
        self.assertEqual(t2._previous_transaction, t1)

        # Create a third transaction, this should link to the second one
        t3 = self.account.transactions.create(
            amount=7, description="test", transaction_type="test", processor=self.user
        )
        self.account.refresh_from_db()

        self.assertEqual(self.account.transactions.last(), t3)
        self.assertEqual(self.account.balance, 22)
        self.assertEqual(self.account.transactions.count(), 3)
        self.assertEqual(t3._balance_after, 22)
        self.assertEqual(t3._previous_transaction, t2)

        self.assertEqual(self.account.transactions.first(), t1)
        self.assertEqual(self.account.transactions.last(), t3)

        # Delete an old transaction, this shouldn't affect the balance
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
        t4 = self.account.transactions.create(
            amount=2, description="test", transaction_type="test", processor=self.user
        )
        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, 24)
        self.assertEqual(self.account.transactions.count(), 3)
        self.assertEqual(t4._balance_after, 24)
        self.assertEqual(t4._previous_transaction, t3)

        # Delete the transaction at the end, this should affect the balance
        t4.delete()
        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, 22)
        self.assertEqual(self.account.transactions.count(), 2)

        t5 = self.account.transactions.create(
            amount=9, description="test", transaction_type="test", processor=self.user
        )
        self.account.refresh_from_db()

        self.assertEqual(self.account.balance, 31)
        self.assertEqual(self.account.transactions.count(), 3)
        self.assertEqual(t5._balance_after, 31)
        self.assertEqual(t5._previous_transaction, t3)

        # Delete the transaction in the middle, this shouldn't affect the balance, but it deletes all transactions
        # before it
        t3.delete()
        self.account.refresh_from_db()
        t5.refresh_from_db()

        self.assertEqual(self.account.balance, 31)
        self.assertEqual(self.account.transactions.count(), 1)
        self.assertEqual(self.account.transactions.first(), t5)
        self.assertEqual(self.account.transactions.last(), t5)
        self.assertEqual(t5._previous_transaction, None)
        self.assertEqual(t5._balance_after, 31)

    def test_create_invalid_history_transaction(self):
        t1 = self.account.transactions.create(
            amount=10, description="test", transaction_type="test", processor=self.user
        )
        self.account.transactions.create(amount=5, description="test", transaction_type="test", processor=self.user)

        with self.assertRaises(IntegrityError):
            self.account.transactions.create(
                amount=7, description="test", transaction_type="test", processor=self.user, _previous_transaction=t1
            )

    def test_create_invalid_balance_transaction(self):
        self.account.transactions.create(amount=10, description="test", transaction_type="test", processor=self.user)
        self.account.transactions.create(amount=5, description="test", transaction_type="test", processor=self.user)

        with self.assertRaises(IntegrityError):
            self.account.transactions.create(
                amount=7, description="test", transaction_type="test", processor=self.user, _balance_after=20
            )
