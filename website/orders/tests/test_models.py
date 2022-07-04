import datetime
import logging
from datetime import timedelta
from unittest.mock import patch, MagicMock
from freezegun import freeze_time

import pytz
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.conf import settings

from orders import models
from venues.models import Venue


User = get_user_model()
logging.disable()


class OrderModelTests(TestCase):

    fixtures = ["venues.json", "users.json"]

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = User.objects.get(pk=2)
        cls.admin_user = User.objects.get(pk=1)
        venue_pk_1 = Venue.objects.get(pk=1)
        order_venue = models.OrderVenue.objects.create(venue=venue_pk_1)
        cls.order_venue = order_venue
        cls.product = models.Product.objects.create(name="Test product", current_price=1.25)
        cls.product_2 = models.Product.objects.create(name="Test product 2", current_price=2.00)
        cls.shift = models.Shift.objects.create(
            venue=order_venue, start=timezone.now(), end=timezone.now() + timedelta(hours=4)
        )

    def setUp(self):
        self.product.available_at.add(self.order_venue)
        self.product.save()
        self.product_2.available_at.add(self.order_venue)
        self.product_2.save()

    def test_validate_barcode(self):
        with self.subTest("Valid barcodes"):
            models.validate_barcode("8710624356910")
            models.validate_barcode("5449000000439")
            models.validate_barcode("61940017")
            models.validate_barcode("87654325")
            models.validate_barcode(None)

        with self.subTest("Invalid barcodes"):
            self.assertRaises(ValidationError, models.validate_barcode, "8710624356915")
            self.assertRaises(ValidationError, models.validate_barcode, "87106243569")
            self.assertRaises(ValidationError, models.validate_barcode, "87C062B356A")

    def test_default_start_time_shift(self):
        start_time = models.get_default_start_time_shift()
        timezone_pytz = pytz.timezone(settings.TIME_ZONE)
        self.assertEqual(
            start_time, timezone.now().astimezone(timezone_pytz).replace(hour=12, minute=15, second=0, microsecond=0)
        )

    def test_default_end_time_shift(self):
        end_time = models.get_default_end_time_shift()
        timezone_pytz = pytz.timezone(settings.TIME_ZONE)
        self.assertEqual(
            end_time, timezone.now().astimezone(timezone_pytz).replace(hour=13, minute=15, second=0, microsecond=0)
        )

    def test_order_venue_str(self):
        self.assertEqual(self.order_venue.__str__(), "Noordkantine")

    def test_product_str(self):
        self.assertEqual(self.product.__str__(), "Test product")

    def test_product_user_order_amount(self):
        product = models.Product.objects.create(name="Test no restriction", max_allowed_per_shift=2, current_price=0.8)
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift))
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        self.assertFalse(product.user_can_order_amount(self.normal_user, self.shift, amount=3))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=product)
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift))
        self.assertFalse(product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift))

    def test_product_user_order_amount_no_restriction(self):
        product = models.Product.objects.create(
            name="Test no restriction", max_allowed_per_shift=None, current_price=0.8
        )
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift))
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift, amount=3))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=product)
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift))
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertTrue(product.user_can_order_amount(self.normal_user, self.shift, amount=2))

    def test_product_user_max_order_amount(self):
        product = models.Product.objects.create(name="Test no restriction", max_allowed_per_shift=2, current_price=0.8)
        self.assertEqual(product.user_max_order_amount(self.normal_user, self.shift), 2)
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=product)
        self.assertEqual(product.user_max_order_amount(self.normal_user, self.shift), 1)
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertEqual(product.user_max_order_amount(self.normal_user, self.shift), 1)

    def test_product_user_max_order_amount_no_restriction(self):
        product = models.Product.objects.create(
            name="Test no restriction", max_allowed_per_shift=None, current_price=0.8
        )
        self.assertEqual(product.user_max_order_amount(self.normal_user, self.shift), None)
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=product)
        self.assertEqual(product.user_max_order_amount(self.normal_user, self.shift), None)
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertEqual(product.user_max_order_amount(self.normal_user, self.shift), None)

    def test_active_venue_validator(self):
        self.assertTrue(self.order_venue.venue.active)
        self.assertTrue(models.active_venue_validator(self.order_venue))
        self.order_venue.venue.active = False
        self.order_venue.venue.save()
        self.assertRaises(ValidationError, models.active_venue_validator, self.order_venue)

    def test_shift_str(self):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        self.assertEqual(shift.__str__(), "{} {}".format(self.order_venue, shift.date))

    @patch("orders.models.Shift._clean")
    @patch("orders.models.Shift._make_finalized")
    def test_shift_save(self, _make_finalized_mock, _clean_mock):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        shift.finalized = True
        shift.save()
        _make_finalized_mock.assert_called()

    @patch("orders.models.Shift._clean")
    @patch("orders.models.Shift._make_finalized")
    def test_shift_save_not_finalized(self, _make_finalized_mock, _clean_mock):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        shift.finalized = False
        shift.save()
        _make_finalized_mock.assert_not_called()

    @patch("orders.models.Shift._clean")
    @patch("orders.models.Shift._make_finalized")
    def test_shift_save_create_finalized(self, _make_finalized_mock, _clean_mock):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        models.Shift.objects.create(venue=self.order_venue, start=start, end=end, finalized=True)
        _make_finalized_mock.assert_called()

    def test_shift_number_of_restricted_orders(self):
        self.assertEqual(self.shift.number_of_restricted_orders, 0)
        models.Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
        self.assertEqual(self.shift.number_of_restricted_orders, 1)
        product_unrestricted = models.Product.objects.create(
            name="Unrestricted product", current_price=5, ignore_shift_restrictions=True
        )
        models.Order.objects.create(user=self.normal_user, product=product_unrestricted, shift=self.shift)
        self.assertEqual(self.shift.number_of_restricted_orders, 1)

    def test_shift_number_of_orders(self):
        self.assertEqual(self.shift.number_of_orders, 0)
        models.Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
        self.assertEqual(self.shift.number_of_orders, 1)
        product_unrestricted = models.Product.objects.create(
            name="Unrestricted product", current_price=5, ignore_shift_restrictions=True
        )
        models.Order.objects.create(user=self.normal_user, product=product_unrestricted, shift=self.shift)
        self.assertEqual(self.shift.number_of_orders, 2)

    def test_shift_max_orders_total_string(self):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, max_orders_total=13)
        self.assertEqual(shift.max_orders_total_string, "{}".format(shift.max_orders_total))
        shift.max_orders_total = None
        shift.save()
        self.assertEqual(shift.max_orders_total_string, "∞")

    def test_shift_capacity(self):
        self.assertEqual(self.shift.capacity, "{} / {}".format(0, self.shift.max_orders_total_string))
        models.Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
        self.assertEqual(self.shift.capacity, "{} / {}".format(1, self.shift.max_orders_total_string))
        product_unrestricted = models.Product.objects.create(
            name="Unrestricted product", current_price=5, ignore_shift_restrictions=True
        )
        models.Order.objects.create(user=self.normal_user, product=product_unrestricted, shift=self.shift)
        self.assertEqual(self.shift.capacity, "{} / {}".format(2, self.shift.max_orders_total_string))

    def test_shift_is_active(self):
        self.assertTrue(self.shift.is_active)
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, max_orders_total=13)
        self.assertFalse(shift.is_active)

    def test_shift_date(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        self.assertEqual(shift.date, "2022-03-04")
        shift.end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=5, hour=13, minute=30))
        shift.save()
        self.assertEqual(shift.date, "2022-03-04 - 2022-03-05")

    def test_shift_start_time(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        self.assertEqual(shift.start_time, "12:15")

    def test_shift_end_time(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        self.assertEqual(shift.end_time, "13:30")

    @freeze_time("2022-04-03")
    def test_shift_human_readable_start_end_time(self):
        current_timezone = pytz.timezone(settings.TIME_ZONE)

        with self.subTest("Start end on same day"):
            start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
            end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
            shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
            self.assertEqual(
                shift.human_readable_start_end_time,
                "{}, 12:15 until 13:30".format(start.strftime(models.Shift.HUMAN_DATE_FORMAT)),
            )

        with self.subTest("Start end on today date"):
            venue_2 = Venue.objects.get(pk=2)
            order_venue_2 = models.OrderVenue.objects.create(venue=venue_2)
            start_today = (
                timezone.now().astimezone(current_timezone).replace(hour=12, minute=30, second=0, microsecond=0)
            )
            end_today = (
                timezone.now().astimezone(current_timezone).replace(hour=13, minute=30, second=0, microsecond=0)
            )
            shift_2 = models.Shift.objects.create(venue=order_venue_2, start=start_today, end=end_today)
            self.assertEqual(shift_2.human_readable_start_end_time, "12:30 until 13:30")

        with self.subTest("Start today, end tomorrow"):
            tomorrow = timezone.now().astimezone(current_timezone).replace(
                hour=13, minute=30, second=0, microsecond=0
            ) + timedelta(days=1)
            shift_2.end = tomorrow
            shift_2.save()
            self.assertEqual(
                shift_2.human_readable_start_end_time,
                "12:30 until {}, 13:30".format(tomorrow.strftime(models.Shift.HUMAN_DATE_FORMAT)),
            )

        with self.subTest("Start and end both not today"):
            day_after_tomorrow = tomorrow + timedelta(days=1)
            shift_2.start = tomorrow
            shift_2.end = day_after_tomorrow
            shift_2.save()
            self.assertEqual(
                shift_2.human_readable_start_end_time,
                "{}, 13:30 until {}, 13:30".format(
                    tomorrow.strftime(models.Shift.HUMAN_DATE_FORMAT),
                    day_after_tomorrow.strftime(models.Shift.HUMAN_DATE_FORMAT),
                ),
            )

    @freeze_time("2022-04-03")
    def test_shift__make_finalized(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=4, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=4, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        self.assertEqual(shift.end, end)
        shift._make_finalized()
        self.assertEqual(
            shift.end.timestamp(), timezone.make_aware(datetime.datetime(year=2022, month=4, day=3)).timestamp()
        )
        self.assertFalse(shift.can_order)

    def test_shift_shift_done(self):
        self.assertTrue(self.shift.shift_done)
        order = models.Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
        self.assertFalse(self.shift.shift_done)
        order.paid = True
        order.ready = True
        order.save()
        self.assertTrue(self.shift.shift_done)
        models.Order.objects.create(
            user=self.normal_user, product=self.product, shift=self.shift, type=models.Order.TYPE_SCANNED
        )
        self.assertTrue(self.shift.shift_done)

    def test_shift__clean_no_venue_id(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        shift.venue = None
        self.assertRaises(ValidationError, shift._clean)

    def test_shift__clean_unfinalize(self, *args):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, finalized=True)
        shift.finalized = False
        self.assertRaises(ValidationError, shift._clean)

    def test_shift__clean_change_finalized_shift(self, *args):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, finalized=True)
        shift.max_orders_per_user = 15
        self.assertRaises(ValidationError, shift._clean)

    def test_shift__clean_finalized_not_done_shift(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        models.Order.objects.create(user=self.normal_user, product=self.product, shift=shift)
        shift.finalized = True
        self.assertRaises(ValidationError, shift._clean)

    def test_shift__clean_end_before_start(self, *args):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
        shift.end = start - timedelta(hours=1)
        self.assertRaises(ValidationError, shift._clean)

    def test_shift__clean_overlapping_shifts(self):
        venue_2 = Venue.objects.get(pk=2)
        order_venue_2 = models.OrderVenue.objects.create(venue=venue_2)
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        models.Shift.objects.create(venue=self.order_venue, start=start, end=end)

        with self.subTest("Shift inside other shift"):
            start_shift_inside_other_shift = timezone.make_aware(
                datetime.datetime(year=2022, month=3, day=2, hour=12, minute=30)
            )
            end_shift_inside_other_shift = timezone.make_aware(
                datetime.datetime(year=2022, month=3, day=2, hour=13, minute=15)
            )
            shift_inside_other_shift = models.Shift.objects.create(
                venue=order_venue_2, start=start_shift_inside_other_shift, end=end_shift_inside_other_shift
            )
            shift_inside_other_shift.venue = self.order_venue
            self.assertRaises(ValidationError, shift_inside_other_shift._clean)
            shift_inside_other_shift.delete()

        with self.subTest("Shift before other shift overlapping"):
            start_shift_before_other_shift = timezone.make_aware(
                datetime.datetime(year=2022, month=3, day=2, hour=11, minute=30)
            )
            end_shift_before_other_shift = timezone.make_aware(
                datetime.datetime(year=2022, month=3, day=2, hour=12, minute=45)
            )
            shift_before_other_shift = models.Shift.objects.create(
                venue=order_venue_2, start=start_shift_before_other_shift, end=end_shift_before_other_shift
            )
            shift_before_other_shift.venue = self.order_venue
            self.assertRaises(ValidationError, shift_before_other_shift._clean)
            shift_before_other_shift.delete()

        with self.subTest("Shift after other shift overlapping"):
            start_shift_after_other_shift = timezone.make_aware(
                datetime.datetime(year=2022, month=3, day=2, hour=13, minute=15)
            )
            end_shift_after_other_shift = timezone.make_aware(
                datetime.datetime(year=2022, month=3, day=2, hour=14, minute=45)
            )
            shift_after_other_shift = models.Shift.objects.create(
                venue=order_venue_2, start=start_shift_after_other_shift, end=end_shift_after_other_shift
            )
            shift_after_other_shift.venue = self.order_venue
            self.assertRaises(ValidationError, shift_before_other_shift._clean)

    @patch("orders.models.Shift._clean")
    def test_shift_clean(self, _clean_mock: MagicMock):
        self.shift.clean()
        _clean_mock.assert_called()

    def test_shift_user_can_order_amount(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, max_orders_per_user=None)
        self.assertTrue(shift.user_can_order_amount(self.normal_user, 15))
        shift.max_orders_per_user = 2
        shift.save()
        models.Order.objects.create(user=self.normal_user, shift=shift, product=self.product)
        self.assertTrue(shift.user_can_order_amount(self.normal_user))
        self.assertFalse(shift.user_can_order_amount(self.normal_user, 2))
        models.Order.objects.create(user=self.normal_user, shift=shift, product=self.product)
        self.assertFalse(shift.user_can_order_amount(self.normal_user))

    def test_shift_max_order_amount(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, max_orders_per_user=None)
        self.assertIsNone(shift.user_max_order_amount(self.normal_user))
        shift.max_orders_per_user = 2
        shift.save()
        models.Order.objects.create(user=self.normal_user, shift=shift, product=self.product)
        self.assertEqual(shift.user_max_order_amount(self.normal_user), 1)
        models.Order.objects.create(user=self.normal_user, shift=shift, product=self.product)
        self.assertEqual(shift.user_max_order_amount(self.normal_user), 0)

    def test_available_product_filter(self):
        test_product_available = models.Product.objects.create(
            name="Available product", current_price=0.99, available=True
        )
        test_product_unavailable = models.Product.objects.create(
            name="Unavailable product", current_price=1.45, available=False
        )
        self.assertTrue(models.available_product_filter(test_product_available.pk))
        self.assertRaises(ValidationError, models.available_product_filter, test_product_unavailable.pk)
        self.assertTrue(models.available_product_filter(test_product_available))
        self.assertRaises(ValidationError, models.available_product_filter, test_product_unavailable)

    def test_order___str__(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        self.assertEqual(order.__str__(), "{} for {} ({})".format(self.product, self.normal_user, self.shift))

    def test_order_save(self, *args):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=2, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end, max_orders_per_user=None)
        order = models.Order.objects.create(
            user=self.normal_user, shift=shift, product=self.product, paid=True, ready=True
        )
        self.assertEqual(order.order_price, self.product.current_price)
        shift.finalized = True
        shift.save()
        order.order_price = 5
        self.assertRaises(ValidationError, order.save)

    def test_order_venue(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        self.assertEqual(order.venue, self.shift.venue)

    def test_order_done(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        self.assertFalse(order.done)
        order.paid = True
        self.assertFalse(order.done)
        order.ready = True
        self.assertTrue(order.done)
