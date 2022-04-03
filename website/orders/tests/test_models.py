import datetime
from datetime import timedelta
from unittest.mock import patch
from freezegun import freeze_time

import pytz
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.conf import settings
from guardian.shortcuts import assign_perm

from orders import models
from venues.models import Venue


User = get_user_model()


class OrderModelTests(TestCase):

    fixtures = ["venues.json", "users.json"]

    def setUp(self):
        self.normal_user = User.objects.get(pk=2)
        venue_pk_1 = Venue.objects.get(pk=1)
        self.order_venue = models.OrderVenue.objects.create(venue=venue_pk_1)
        self.product = models.Product.objects.create(name="Test product", current_price=1.25)
        self.product.available_at.add(self.order_venue)
        self.product.save()
        self.product_2 = models.Product.objects.create(name="Test product 2", current_price=2.00)
        self.product_2.available_at.add(self.order_venue)
        self.product_2.save()
        self.shift = models.Shift.objects.create(
            venue=self.order_venue, start_date=timezone.now(), end_date=timezone.now() + timedelta(hours=4)
        )

    def test_validate_barcode(self):
        def barcode_wrong_checksum():
            models.validate_barcode("8710624356915")

        def barcode_too_short():
            models.validate_barcode("87106243569")

        def barcode_not_only_digits():
            models.validate_barcode("87C062B356A")

        models.validate_barcode("8710624356910")
        models.validate_barcode("5449000000439")
        models.validate_barcode("61940017")
        models.validate_barcode("87654325")
        models.validate_barcode(None)
        self.assertRaises(ValidationError, barcode_wrong_checksum)
        self.assertRaises(ValidationError, barcode_too_short)
        self.assertRaises(ValidationError, barcode_not_only_digits)

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

    def test_order_venue_users_shift_admin_perms(self):
        self.assertEqual(len(self.order_venue.get_users_with_shift_admin_perms()), 1)
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue)
        users_with_admin_perms = self.order_venue.get_users_with_shift_admin_perms()
        self.assertEqual(len(users_with_admin_perms), 2)
        self.assertTrue(self.normal_user in users_with_admin_perms)

    def test_order_venue_users_shift_admin_perms_queryset(self):
        self.assertEqual(len(self.order_venue.get_users_with_shift_admin_perms_queryset()), 1)
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue)
        users_with_admin_perms = self.order_venue.get_users_with_shift_admin_perms_queryset()
        self.assertEqual(len(users_with_admin_perms), 2)
        self.assertTrue(self.normal_user in users_with_admin_perms)

    def test_order_venue_users_shift_order_perms(self):
        self.assertEqual(len(self.order_venue.get_users_with_order_perms()), 1)
        assign_perm("orders.can_order_in_venue", self.normal_user, self.order_venue)
        users_with_order_perms = self.order_venue.get_users_with_order_perms()
        self.assertEqual(len(users_with_order_perms), 2)
        self.assertTrue(self.normal_user in users_with_order_perms)

    def test_order_venue_users_shift_order_perms_queryset(self):
        self.assertEqual(len(self.order_venue.get_users_with_order_perms_queryset()), 1)
        assign_perm("orders.can_order_in_venue", self.normal_user, self.order_venue)
        users_with_order_perms = self.order_venue.get_users_with_order_perms_queryset()
        self.assertEqual(len(users_with_order_perms), 2)
        self.assertTrue(self.normal_user in users_with_order_perms)

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

        def do_raise_validation_error():
            models.active_venue_validator(self.order_venue)

        self.assertRaises(ValidationError, do_raise_validation_error)

    def test_shift_str(self):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(shift.__str__(), "{} {}".format(self.order_venue, shift.date))

    @patch("orders.models.Shift._clean")
    @patch("orders.models.Shift._make_finalized")
    @patch("tantalus.signals.synchronize_to_tantalus")
    def test_shift_save(self, _synchronize_to_tantalus_mock, _make_finalized_mock, _clean_mock):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        shift.finalized = True
        shift.save()
        _make_finalized_mock.assert_called()

    @patch("orders.models.Shift._clean")
    @patch("orders.models.Shift._make_finalized")
    @patch("tantalus.signals.synchronize_to_tantalus")
    def test_shift_save_not_finalized(self, _synchronize_to_tantalus_mock, _make_finalized_mock, _clean_mock):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        shift.finalized = False
        shift.save()
        _make_finalized_mock.assert_not_called()

    @patch("orders.models.Shift._clean")
    @patch("orders.models.Shift._make_finalized")
    @patch("tantalus.signals.synchronize_to_tantalus")
    def test_shift_save_create_finalized(self, _synchronize_to_tantalus_mock, _make_finalized_mock, _clean_mock):
        start = timezone.now() + timedelta(days=1)
        end = timezone.now() + timedelta(days=1, hours=4)
        models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end, finalized=True)
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
        shift = models.Shift.objects.create(
            venue=self.order_venue, start_date=start, end_date=end, max_orders_total=13
        )
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
        shift = models.Shift.objects.create(
            venue=self.order_venue, start_date=start, end_date=end, max_orders_total=13
        )
        self.assertFalse(shift.is_active)

    def test_shift_date(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(shift.date, "2022-03-04")
        shift.end_date = timezone.make_aware(datetime.datetime(year=2022, month=3, day=5, hour=13, minute=30))
        shift.save()
        self.assertEqual(shift.date, "2022-03-04 - 2022-03-05")

    def test_shift_start_time(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(shift.start_time, "12:15")

    def test_shift_end_time(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(shift.end_time, "13:30")

    @freeze_time("2022-04-03")
    def test_shift_human_readable_start_end_time(self):
        current_timezone = pytz.timezone(settings.TIME_ZONE)
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(
            shift.human_readable_start_end_time,
            "{}, 12:15 until 13:30".format(start.strftime(models.Shift.HUMAN_DATE_FORMAT)),
        )
        venue_2 = Venue.objects.get(pk=2)
        order_venue_2 = models.OrderVenue.objects.create(venue=venue_2)
        start_today = timezone.now().astimezone(current_timezone).replace(hour=12, minute=30, second=0, microsecond=0)
        end_today = timezone.now().astimezone(current_timezone).replace(hour=13, minute=30, second=0, microsecond=0)
        shift_2 = models.Shift.objects.create(venue=order_venue_2, start_date=start_today, end_date=end_today)
        self.assertEqual(shift_2.human_readable_start_end_time, "12:30 until 13:30")
        tomorrow = timezone.now().astimezone(current_timezone).replace(
            hour=13, minute=30, second=0, microsecond=0
        ) + timedelta(days=1)
        shift_2.end_date = tomorrow
        shift_2.save()
        self.assertEqual(
            shift_2.human_readable_start_end_time,
            "12:30 until {}, 13:30".format(tomorrow.strftime(models.Shift.HUMAN_DATE_FORMAT)),
        )
        day_after_tomorrow = tomorrow + timedelta(days=1)
        shift_2.start_date = tomorrow
        shift_2.end_date = day_after_tomorrow
        shift_2.save()
        self.assertEqual(
            shift_2.human_readable_start_end_time,
            "{}, 13:30 until {}, 13:30".format(
                tomorrow.strftime(models.Shift.HUMAN_DATE_FORMAT),
                day_after_tomorrow.strftime(models.Shift.HUMAN_DATE_FORMAT),
            ),
        )

    def test_shift_get_users_with_change_perms(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(len(shift.get_users_with_change_perms()), 1)
        self.assertFalse(self.normal_user in shift.get_users_with_change_perms())
        assign_perm("orders.change_shift", self.normal_user, shift)
        self.assertTrue(self.normal_user in shift.get_users_with_change_perms())

    @override_settings(TIME_ZONE="UTC")
    def test_shift__make_finalized(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertEqual(shift.end_date, end)
        now = timezone.now()
        with freeze_time(now):
            shift._make_finalized()
            self.assertEqual(shift.end_date.timestamp(), now.timestamp())
            self.assertFalse(shift.can_order)
