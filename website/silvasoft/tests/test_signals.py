from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from associations.models import Association
from orders.models import OrderVenue, Shift, Product as OrdersProduct
from borrel.models import BorrelReservation, ReservationItem, Product as BorrelProduct
from silvasoft.models import SilvasoftAssociation, SilvasoftBorrelProduct
from venues.models import Venue

User = get_user_model()


class SilvasoftSignalsTest(TestCase):
    fixtures = [
        "users.json",
        "venues.json",
        "associations.json",
        "borrel.json",
        "silvasoft.json",
    ]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(pk=1)
        association = Association.objects.get(pk=1)
        cls.silvasoft_association = SilvasoftAssociation.objects.get(
            association=association
        )
        cls.association = association
        borrel_product_1 = BorrelProduct.objects.get(pk=1)
        borrel_product_2 = BorrelProduct.objects.get(pk=2)
        borrel_product_3 = BorrelProduct.objects.get(pk=3)
        borrel_product_4 = BorrelProduct.objects.get(pk=4)
        borrel_product_5 = BorrelProduct.objects.get(pk=5)
        borrel_product_6 = BorrelProduct.objects.get(pk=6)
        cls.silvasoft_product_1 = SilvasoftBorrelProduct.objects.get(
            product=borrel_product_1
        )
        cls.silvasoft_product_2 = SilvasoftBorrelProduct.objects.get(
            product=borrel_product_2
        )
        cls.silvasoft_product_3 = SilvasoftBorrelProduct.objects.get(
            product=borrel_product_3
        )
        cls.silvasoft_product_4 = SilvasoftBorrelProduct.objects.get(
            product=borrel_product_4
        )
        cls.silvasoft_product_6 = SilvasoftBorrelProduct.objects.get(
            product=borrel_product_6
        )
        cls.borrel_product_1 = borrel_product_1
        cls.borrel_product_2 = borrel_product_2
        cls.borrel_product_3 = borrel_product_3
        cls.borrel_product_4 = borrel_product_4
        cls.borrel_product_5 = borrel_product_5
        cls.borrel_product_6 = borrel_product_6

        venue_pk_1 = Venue.objects.get(pk=1)
        order_venue = OrderVenue.objects.create(venue=venue_pk_1)
        cls.order_venue = order_venue
        cls.orders_product_1 = OrdersProduct.objects.create(
            name="Test product", current_price=1.25
        )
        cls.orders_product_2 = OrdersProduct.objects.create(
            name="Test product 2", current_price=2.00
        )
        cls.shift = Shift.objects.create(
            venue=order_venue,
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=4),
        )

    def setUp(self):
        self.borrel_reservation = BorrelReservation.objects.create(
            title="Test Borrel Reservation",
            start=timezone.now() + timedelta(hours=2),
            end=timezone.now() + timedelta(hours=8),
            user_created=self.user,
            user_updated=self.user,
            association=self.association,
        )
        self.reservation_item_1 = ReservationItem.objects.create(
            reservation=self.borrel_reservation,
            product=self.borrel_product_1,
            amount_reserved=5,
        )
        self.reservation_item_2 = ReservationItem.objects.create(
            reservation=self.borrel_reservation,
            product=self.borrel_product_2,
            amount_reserved=18,
        )
        self.reservation_item_3 = ReservationItem.objects.create(
            reservation=self.borrel_reservation,
            product=self.borrel_product_3,
            amount_reserved=9,
        )
        self.reservation_item_4 = ReservationItem.objects.create(
            reservation=self.borrel_reservation,
            product=self.borrel_product_4,
            amount_reserved=1,
        )
        self.reservation_items = [
            self.reservation_item_1,
            self.reservation_item_2,
            self.reservation_item_3,
            self.reservation_item_4,
        ]

    def set_amounts_used(self):
        for reservation_item in self.reservation_items:
            reservation_item.amount_used = reservation_item.amount_reserved
            reservation_item.save()

    def test_pre_save_shift_sets_cache_property(self):
        """Test whether the `pre_save` method sets the `_object_pre_save` property."""
        self.shift.finalized = True
        self.shift.save()
        self.assertIsNotNone(self.shift._object_pre_save)
        self.assertFalse(self.shift._object_pre_save.finalized)

    def test_pre_save_borrel_reservation_sets_cache_property(self):
        """Test whether the `pre_save` method sets the `_object_pre_save` property."""
        self.borrel_reservation.submitted_at = timezone.now()
        self.borrel_reservation.save()
        self.assertIsNotNone(self.borrel_reservation._object_pre_save)
        self.assertIsNone(self.borrel_reservation._object_pre_save.submitted_at)

    @patch("silvasoft.signals.task_synchronize_shift_to_silvasoft.delay")
    def test_shift_sync_job_spawned_when_finalized(
        self, task_synchronize_shift_to_silvasoft_mock: MagicMock
    ):
        """Test whether the `pre_save` method sets the `_object_pre_save` property."""
        self.shift.finalized = True
        self.shift.save()
        task_synchronize_shift_to_silvasoft_mock.assert_called()
        mock_call = task_synchronize_shift_to_silvasoft_mock.mock_calls.pop()
        self.assertEqual(mock_call.args[0], self.shift.pk)

    @patch("silvasoft.signals.task_synchronize_borrel_reservation_to_silvasoft.delay")
    def test_borrel_reservation_sync_job_spawned_when_submitted(
        self, task_synchronize_borrel_reservation_to_silvasoft: MagicMock
    ):
        """Test whether the `pre_save` method sets the `_object_pre_save` property."""
        self.borrel_reservation.submitted_at = timezone.now()
        self.borrel_reservation.save()
        task_synchronize_borrel_reservation_to_silvasoft.assert_called()
        mock_call = task_synchronize_borrel_reservation_to_silvasoft.mock_calls.pop()
        self.assertEqual(mock_call.args[0], self.borrel_reservation.pk)
