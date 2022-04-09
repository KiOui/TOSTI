import datetime
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from guardian.shortcuts import assign_perm

from orders import services
from orders import models
from venues.models import Venue


User = get_user_model()


class OrderServicesTests(TestCase):

    fixtures = ["users.json", "venues.json"]

    def setUp(self):
        venue_pk_1 = Venue.objects.get(pk=1)
        self.order_venue = models.OrderVenue.objects.create(venue=venue_pk_1)
        self.shift = models.Shift.objects.create(
            venue=self.order_venue, start_date=timezone.now(), end_date=timezone.now() + timedelta(hours=4)
        )
        self.product = models.Product.objects.create(name="Test product", current_price=1.25)
        self.product.available_at.add(self.order_venue)
        self.product.save()
        self.normal_user = User.objects.get(pk=2)

    @patch("orders.services.logging")
    def test_execute_data_minimisation(self, *args):
        order_do_not_delete = models.Order.objects.create(
            shift=self.shift, product=self.product, user=self.normal_user, paid=True
        )
        order_do_delete = models.Order.objects.create(
            shift=self.shift, product=self.product, user=self.normal_user, paid=True
        )
        order_not_paid = models.Order.objects.create(shift=self.shift, product=self.product, user=self.normal_user)
        order_do_delete.created = timezone.now() - timedelta(days=60)
        order_do_delete.save()
        order_not_paid.created = timezone.now() - timedelta(days=60)
        order_not_paid.save()
        services.execute_data_minimisation(dry_run=True)
        self.assertTrue(models.Order.objects.filter(id=order_do_delete.id, user=self.normal_user).exists())
        self.assertTrue(models.Order.objects.filter(id=order_do_not_delete.id, user=self.normal_user).exists())
        self.assertTrue(models.Order.objects.filter(id=order_not_paid.id, user=self.normal_user).exists())
        services.execute_data_minimisation()
        self.assertFalse(models.Order.objects.filter(id=order_do_delete.id, user=self.normal_user).exists())
        self.assertTrue(models.Order.objects.filter(id=order_do_not_delete.id, user=self.normal_user).exists())
        self.assertTrue(models.Order.objects.filter(id=order_not_paid.id, user=self.normal_user).exists())

    def test_add_user_to_assignees_of_shift(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertFalse(shift.assignees.filter(id=self.normal_user.id).exists())

        def throws_exception():
            services.add_user_to_assignees_of_shift(self.normal_user, shift)

        self.assertRaises(PermissionError, throws_exception)
        self.assertFalse(shift.assignees.filter(id=self.normal_user.id).exists())
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue)
        services.add_user_to_assignees_of_shift(self.normal_user, shift)
        self.assertTrue(shift.assignees.filter(id=self.normal_user.id).exists())
        services.add_user_to_assignees_of_shift(self.normal_user, shift)
        self.assertTrue(shift.assignees.filter(id=self.normal_user.id).exists())

    def test_set_shift_active(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        services.set_shift_active(shift, True)
        self.assertTrue(models.Shift.objects.get(id=shift.id).can_order)
        services.set_shift_active(shift, False)
        self.assertFalse(models.Shift.objects.get(id=shift.id).can_order)

    def test_set_order_ready(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        services.set_order_ready(order, True)
        self.assertTrue(models.Order.objects.get(id=order.id).ready)
        services.set_order_ready(order, False)
        self.assertFalse(models.Order.objects.get(id=order.id).ready)

    def test_set_order_paid(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        services.set_order_paid(order, True)
        self.assertTrue(models.Order.objects.get(id=order.id).paid)
        services.set_order_paid(order, False)
        self.assertFalse(models.Order.objects.get(id=order.id).paid)

    def test_increase_shift_capacity(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        start_capacity = shift.max_orders_total
        services.increase_shift_capacity(shift)
        self.assertEqual(models.Shift.objects.get(id=shift.id).max_orders_total, start_capacity + 5)
        services.increase_shift_capacity(shift, 13)
        self.assertEqual(models.Shift.objects.get(id=shift.id).max_orders_total, start_capacity + 18)

    @override_settings(TIME_ZONE="UTC")
    def test_increase_shift_time(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        services.increase_shift_time(shift)
        self.assertEqual(models.Shift.objects.get(id=shift.id).end_date, end + timedelta(minutes=5))
        services.increase_shift_time(shift, 13)
        self.assertEqual(models.Shift.objects.get(id=shift.id).end_date, end + timedelta(minutes=18))
