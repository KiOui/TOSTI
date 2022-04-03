from datetime import timedelta

import pytz
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
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
        self.product.max_allowed_per_shift = 2
        self.product.save()
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift))
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        self.assertFalse(self.product.user_can_order_amount(self.normal_user, self.shift, amount=3))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift))
        self.assertFalse(self.product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift))

    def test_product_user_order_amount_no_restriction(self):
        self.product.max_allowed_per_shift = None
        self.product.save()
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift))
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift, amount=3))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift))
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift, amount=2))
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertTrue(self.product.user_can_order_amount(self.normal_user, self.shift, amount=2))

    def test_product_user_max_order_amount(self):
        self.product.max_allowed_per_shift = 2
        self.product.save()
        self.assertEqual(self.product.user_max_order_amount(self.normal_user, self.shift), 2)
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        self.assertEqual(self.product.user_max_order_amount(self.normal_user, self.shift), 1)
        models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product_2)
        self.assertEqual(self.product.user_max_order_amount(self.normal_user, self.shift), 1)
