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
            venue=order_venue, start=timezone.now(), end=timezone.now() + timedelta(hours=4)
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
        shift = models.Shift.objects.create(venue=self.order_venue, start=start, end=end)
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
