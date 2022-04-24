import datetime
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from guardian.shortcuts import assign_perm

from orders import services
from orders import models
from venues.models import Venue


User = get_user_model()
logging.disable()


class OrderServicesTests(TestCase):

    fixtures = ["users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        venue_pk_1 = Venue.objects.get(pk=1)
        order_venue = models.OrderVenue.objects.create(venue=venue_pk_1)
        cls.order_venue = order_venue
        cls.shift = models.Shift.objects.create(
            venue=order_venue, start_date=timezone.now(), end_date=timezone.now() + timedelta(hours=4)
        )
        cls.product = models.Product.objects.create(name="Test product", current_price=1.25)
        cls.normal_user = User.objects.get(pk=2)

    def setUp(self):
        self.product.available_at.add(self.order_venue)
        self.product.save()

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

        with self.subTest("Data minimisation dry run"):
            services.execute_data_minimisation(dry_run=True)
            self.assertTrue(models.Order.objects.filter(id=order_do_delete.id, user=self.normal_user).exists())
            self.assertTrue(models.Order.objects.filter(id=order_do_not_delete.id, user=self.normal_user).exists())
            self.assertTrue(models.Order.objects.filter(id=order_not_paid.id, user=self.normal_user).exists())

        with self.subTest("Normal Data minimisation run"):
            services.execute_data_minimisation()
            self.assertFalse(models.Order.objects.filter(id=order_do_delete.id, user=self.normal_user).exists())
            self.assertTrue(models.Order.objects.filter(id=order_do_not_delete.id, user=self.normal_user).exists())
            self.assertTrue(models.Order.objects.filter(id=order_not_paid.id, user=self.normal_user).exists())

    def test_add_user_to_assignees_of_shift(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        self.assertFalse(shift.assignees.filter(id=self.normal_user.id).exists())

        with self.subTest("Adding a user as assignee without permissions"):
            self.assertRaises(PermissionError, services.add_user_to_assignees_of_shift, self.normal_user, shift)
            self.assertFalse(shift.assignees.filter(id=self.normal_user.id).exists())
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue)

        with self.subTest("Adding a user as assignee with permissions"):
            services.add_user_to_assignees_of_shift(self.normal_user, shift)
            self.assertTrue(shift.assignees.filter(id=self.normal_user.id).exists())

        with self.subTest("Re-adding a user as assignee"):
            services.add_user_to_assignees_of_shift(self.normal_user, shift)
            self.assertTrue(shift.assignees.filter(id=self.normal_user.id).exists())

    def test_set_shift_active(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)

        with self.subTest("Set shift active True"):
            services.set_shift_active(shift, True)
            self.assertTrue(models.Shift.objects.get(id=shift.id).can_order)

        with self.subTest("Set shift active False"):
            services.set_shift_active(shift, False)
            self.assertFalse(models.Shift.objects.get(id=shift.id).can_order)

    def test_set_order_ready(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)

        with self.subTest("Set order ready True"):
            services.set_order_ready(order, True)
            self.assertTrue(models.Order.objects.get(id=order.id).ready)

        with self.subTest("Set order ready False"):
            services.set_order_ready(order, False)
            self.assertFalse(models.Order.objects.get(id=order.id).ready)

    def test_set_order_paid(self):
        order = models.Order.objects.create(user=self.normal_user, shift=self.shift, product=self.product)
        with self.subTest("Set order paid True"):
            services.set_order_paid(order, True)
            self.assertTrue(models.Order.objects.get(id=order.id).paid)

        with self.subTest("Set order paid False"):
            services.set_order_paid(order, False)
            self.assertFalse(models.Order.objects.get(id=order.id).paid)

    def test_increase_shift_capacity(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        start_capacity = shift.max_orders_total
        with self.subTest("Increase shift capacity with default amount"):
            services.increase_shift_capacity(shift)
            self.assertEqual(models.Shift.objects.get(id=shift.id).max_orders_total, start_capacity + 5)

        with self.subTest("Increase shift capacity with custom amount"):
            services.increase_shift_capacity(shift, 13)
            self.assertEqual(models.Shift.objects.get(id=shift.id).max_orders_total, start_capacity + 18)

    def test_increase_shift_time(self):
        start = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=12, minute=15))
        end = timezone.make_aware(datetime.datetime(year=2022, month=3, day=4, hour=13, minute=30))
        shift = models.Shift.objects.create(venue=self.order_venue, start_date=start, end_date=end)
        with self.subTest("Increase shift time with default amount"):
            services.increase_shift_time(shift)
            self.assertEqual(models.Shift.objects.get(id=shift.id).end_date, end + timedelta(minutes=5))

        with self.subTest("Increase shift time with custom amount"):
            services.increase_shift_time(shift, 13)
            self.assertEqual(models.Shift.objects.get(id=shift.id).end_date, end + timedelta(minutes=18))
