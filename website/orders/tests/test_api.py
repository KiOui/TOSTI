import datetime
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from guardian.shortcuts import assign_perm

from rest_framework.test import APITestCase
from orders import models
from orders.models import Order, Shift, OrderVenue
from venues.models import Venue


User = get_user_model()
logging.disable()


class OrderServicesTests(APITestCase):
    fixtures = ["users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        venue_pk_1 = Venue.objects.get(pk=1)
        order_venue = models.OrderVenue.objects.create(venue=venue_pk_1)
        cls.order_venue = order_venue
        cls.shift = models.Shift.objects.create(
            venue=order_venue, start=timezone.now(), end=timezone.now() + timedelta(hours=4), can_order=True
        )
        cls.product = models.Product.objects.create(name="Test product", current_price=1.25)
        cls.product_not_available_at_venue = models.Product.objects.create(
            name="Not available at venue", current_price=0.6
        )
        cls.normal_user = User.objects.get(pk=2)
        cls.normal_user.set_password("password")
        cls.normal_user.save()
        cls.user_with_permissions = User.objects.create(
            username="userwithpermission",
            full_name="User with Permission",
            first_name="User",
            last_name="with Permission",
            email="user@withpermission.com",
            association=None,
            password="unusable",
            is_superuser=False,
            is_staff=True,
            is_active=True,
        )
        cls.user_with_permissions.set_password("password")
        cls.user_with_permissions.save()
        assign_perm("orders.can_manage_shift_in_venue", cls.user_with_permissions, cls.order_venue)
        cls.shift.assignees.add(cls.user_with_permissions)

    def setUp(self):
        self.product.available_at.add(self.order_venue)
        self.product.save()

    def test_list_orders_not_logged_in(self):
        """Listing orders of a Shift should fail if not logged in."""
        Order.objects.create(user=None, product=self.product, shift=self.shift)
        response = self.client.get(reverse("v1:orders_listcreate", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 403)

    def test_list_orders(self):
        """Listing orders of a Shift should fail if not logged in."""
        Order.objects.create(user=None, product=self.product, shift=self.shift)
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.get(reverse("v1:orders_listcreate", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 200)

    def test_create_order_not_logged_in(self):
        """Non-logged in users should not be able to order items."""
        response = self.client.post(reverse("v1:orders_listcreate", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 403)

    def test_create_order_logged_in_normal_user(self):
        """Logged in users should be able to order items."""
        orders_before = Order.objects.all().count()
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        orders_after = Order.objects.all().count()
        self.assertEqual(orders_after - orders_before, 1)
        created_order = Order.objects.latest("id")
        self.assertEqual(created_order.product, self.product)

    def test_create_order_product_not_available_at_venue(self):
        """Products should be available in an order venue in order for orders to be created."""
        with self.subTest("Non privileged user"):
            orders_before = Order.objects.all().count()
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.post(
                reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
                {
                    "product": self.product_not_available_at_venue.id,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 400)
            orders_after = Order.objects.all().count()
            self.assertEqual(orders_after, orders_before)

        with self.subTest("Privileged user"):
            orders_before = Order.objects.all().count()
            self.client.login(username=self.user_with_permissions.username, password="password")
            response = self.client.post(
                reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
                {
                    "product": self.product_not_available_at_venue.id,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 400)
            orders_after = Order.objects.all().count()
            self.assertEqual(orders_after, orders_before)

    def test_create_order_normal_user_ignores_fields(self):
        """When a user does not have privileges, ready and paid attributes are ignored."""
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {"product": self.product.id, "ready": True, "paid": True, "prioritize": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created_order = Order.objects.latest("id")
        self.assertEqual(created_order.product, self.product)
        self.assertEqual(created_order.ready, False)
        self.assertEqual(created_order.paid, False)
        self.assertEqual(created_order.prioritize, False)

    def test_create_order_normal_user_deprioritize(self):
        """Orders can be deprioritized on creation."""
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {"product": self.product.id, "deprioritize": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created_order = Order.objects.latest("id")
        self.assertEqual(created_order.product, self.product)
        self.assertEqual(created_order.deprioritize, True)

    def test_create_order_normal_user_type_scanned(self):
        """When a user has no privilege, the type attribute should be ignored."""
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {"product": self.product.id, "type": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        created_order = Order.objects.latest("id")
        self.assertEqual(created_order.type, 0)

    def test_create_order_closed_shift(self):
        """Orders should not be able to be placed on closed shifts."""
        orders_before = Order.objects.all().count()
        self.shift.can_order = False
        self.shift.save()
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
            },
            format="json",
        )
        orders_after = Order.objects.all().count()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data["detail"]), "This Shift is closed")
        self.assertEqual(orders_before, orders_after)

    @freeze_time()
    def test_create_order_shift_in_future(self):
        """Orders should not be able to be placed on shifts that are starting in the future."""
        self.shift.start = timezone.now() + timedelta(hours=2)
        self.shift.end = timezone.now() + timedelta(hours=4)
        self.shift.save()
        orders_before = Order.objects.all().count()
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
            },
            format="json",
        )
        orders_after = Order.objects.all().count()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data["detail"]), "Shift is not active")
        self.assertEqual(orders_before, orders_after)

    @freeze_time()
    def test_create_order_shift_in_past(self):
        """Orders should not be able to be placed on shifts that are in the past."""
        self.shift.start = timezone.now() - timedelta(hours=4)
        self.shift.end = timezone.now() - timedelta(hours=2)
        self.shift.save()
        orders_before = Order.objects.all().count()
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
            },
            format="json",
        )
        orders_after = Order.objects.all().count()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data["detail"]), "Shift is not active")
        self.assertEqual(orders_before, orders_after)

    @freeze_time()
    def test_create_order_shift_finalized(self):
        """Orders should not be able to be placed on shifts that are finalized."""
        self.shift.start = timezone.now() - timedelta(hours=4)
        self.shift.end = timezone.now() - timedelta(hours=2)
        self.shift.finalized = True
        self.shift.save()
        orders_before = Order.objects.all().count()
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
            },
            format="json",
        )
        orders_after = Order.objects.all().count()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data["detail"]), "Shift is finalized, no Orders can be added anymore")
        self.assertEqual(orders_before, orders_after)

    def test_create_scanned_order(self):
        """A user with privileges can create scanned orders."""
        orders_before = Order.objects.all().count()
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
                "type": 1,
            },
            format="json",
        )
        orders_after = Order.objects.all().count()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(orders_after - orders_before, 1)
        order_created = Order.objects.latest("id")
        self.assertEqual(order_created.type, 1)

    def test_create_normal_order_as_privileged_user(self):
        """A privileged user should be able to create normal orders."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))

        with self.subTest("Explicit type set"):
            orders_before = Order.objects.all().count()
            response = self.client.post(
                reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
                {
                    "product": self.product.id,
                    "type": 0,
                },
                format="json",
            )
            orders_after = Order.objects.all().count()
            self.assertEqual(response.status_code, 201)
            self.assertEqual(orders_after - orders_before, 1)
            order_created = Order.objects.latest("id")
            self.assertEqual(order_created.type, 0)

        with self.subTest("No explicit type set"):
            orders_before = Order.objects.all().count()
            response = self.client.post(
                reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
                {
                    "product": self.product.id,
                },
                format="json",
            )
            orders_after = Order.objects.all().count()
            self.assertEqual(response.status_code, 201)
            self.assertEqual(orders_after - orders_before, 1)
            order_created = Order.objects.latest("id")
            self.assertEqual(order_created.type, 0)

    def test_create_order_made_paid_ready(self):
        """A privileged user should be able to create orders with paid and ready attributes set."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        with self.subTest("Normal order"):
            orders_before = Order.objects.all().count()
            response = self.client.post(
                reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
                {
                    "product": self.product.id,
                    "paid": True,
                    "ready": True,
                },
                format="json",
            )
            orders_after = Order.objects.all().count()
            self.assertEqual(response.status_code, 201)
            self.assertEqual(orders_after - orders_before, 1)
            order_created = Order.objects.latest("id")
            self.assertEqual(order_created.type, 0)
            self.assertEqual(order_created.paid, True)
            self.assertEqual(order_created.ready, True)

        with self.subTest("Scanned order"):
            orders_before = Order.objects.all().count()
            response = self.client.post(
                reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
                {
                    "product": self.product.id,
                    "type": 1,
                    "paid": True,
                    "ready": True,
                },
                format="json",
            )
            orders_after = Order.objects.all().count()
            self.assertEqual(response.status_code, 201)
            self.assertEqual(orders_after - orders_before, 1)
            order_created = Order.objects.latest("id")
            self.assertEqual(order_created.type, 1)
            self.assertEqual(order_created.paid, True)
            self.assertEqual(order_created.ready, True)

    def test_create_order_while_blacklisted(self):
        """Blacklisted users should not be able to order."""
        models.OrderBlacklistedUser.objects.create(user=self.normal_user)
        orders_before = Order.objects.all().count()
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.post(
            reverse("v1:orders_listcreate", kwargs={"shift": self.shift}),
            {
                "product": self.product.id,
            },
            format="json",
        )
        orders_after = Order.objects.all().count()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(orders_after, orders_before)

    def test_full_update_order_not_logged_in(self):
        order = Order.objects.create(user=None, product=self.product, shift=self.shift)
        response = self.client.put(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
            {
                "paid": True,
                "ready": True,
                "deprioritize": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_full_update_order_unprivileged_user(self):
        order = Order.objects.create(user=None, product=self.product, shift=self.shift)
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.put(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
            {
                "paid": True,
                "ready": True,
                "deprioritize": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_full_update_order(self):
        order = Order.objects.create(user=None, product=self.product, shift=self.shift)
        self.client.login(username=self.user_with_permissions.username, password="password")
        response = self.client.put(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
            {
                "paid": True,
                "ready": True,
                "deprioritize": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(pk=order.pk)
        self.assertTrue(order.paid)
        self.assertTrue(order.ready)
        self.assertTrue(order.deprioritize)

    def test_partial_update_order_not_logged_in(self):
        order = Order.objects.create(user=None, product=self.product, shift=self.shift)
        response = self.client.patch(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
            {
                "deprioritize": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_parial_update_order_someone_else(self):
        with self.subTest("Terminal created order"):
            order = Order.objects.create(user=None, product=self.product, shift=self.shift)
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.patch(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
                {
                    "deprioritize": True,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 403)

        with self.subTest("Order someone else"):
            order = Order.objects.create(user=self.user_with_permissions, product=self.product, shift=self.shift)
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.patch(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
                {
                    "deprioritize": True,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 403)

    def test_parial_update_order_normal_user(self):
        with self.subTest("Deprioritize"):
            order = Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.patch(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
                {
                    "deprioritize": True,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            order = Order.objects.get(pk=order.pk)
            self.assertTrue(order.deprioritize)

        with self.subTest("Paid"):
            order = Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.patch(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
                {
                    "paid": True,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 403)
            order = Order.objects.get(pk=order.pk)
            self.assertFalse(order.paid)

        with self.subTest("Ready"):
            order = Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift)
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.patch(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
                {
                    "ready": True,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 403)
            order = Order.objects.get(pk=order.pk)
            self.assertFalse(order.ready)

    def test_partial_update_order_disable_deprioritize(self):
        """For a normal user, disabling deprioritize should not be possible."""
        order = Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift, deprioritize=True)
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.patch(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
            {
                "deprioritize": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        order = Order.objects.get(pk=order.pk)
        self.assertTrue(order.deprioritize)

    def test_partial_update_order_privileged_user(self):
        order = Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift, deprioritize=True)
        self.client.login(username=self.user_with_permissions.username, password="password")
        response = self.client.patch(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk}),
            {
                "deprioritize": False,
                "paid": True,
                "ready": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(pk=order.pk)
        self.assertFalse(order.deprioritize)
        self.assertTrue(order.paid)
        self.assertTrue(order.ready)

    def test_delete_order_not_logged_in(self):
        order = Order.objects.create(user=None, product=self.product, shift=self.shift, deprioritize=True)
        response = self.client.delete(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_order_not_privileged(self):
        order = Order.objects.create(user=self.normal_user, product=self.product, shift=self.shift, deprioritize=True)
        self.client.login(username=self.normal_user.username, password="password")
        response = self.client.delete(
            reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_order(self):
        with self.subTest("Own order"):
            order = Order.objects.create(
                user=self.user_with_permissions, product=self.product, shift=self.shift, deprioritize=True
            )
            self.client.login(username=self.user_with_permissions.username, password="password")
            response = self.client.delete(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk})
            )
            self.assertEqual(response.status_code, 204)

        with self.subTest("Terminal order"):
            order = Order.objects.create(user=None, product=self.product, shift=self.shift, deprioritize=True)
            self.client.login(username=self.user_with_permissions.username, password="password")
            response = self.client.delete(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk})
            )
            self.assertEqual(response.status_code, 204)

        with self.subTest("Other users order"):
            order = Order.objects.create(
                user=self.normal_user, product=self.product, shift=self.shift, deprioritize=True
            )
            self.client.login(username=self.user_with_permissions.username, password="password")
            response = self.client.delete(
                reverse("v1:orders_retrieveupdatedestroy", kwargs={"shift": self.shift, "pk": order.pk})
            )
            self.assertEqual(response.status_code, 204)

    def test_list_shifts(self):
        with self.subTest("Not authenticated"):
            response = self.client.get(reverse("v1:shifts_listcreate"))
            self.assertEqual(response.status_code, 403)
        with self.subTest("Authenticated"):
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.get(reverse("v1:shifts_listcreate"))
            self.assertEqual(response.status_code, 200)

    def test_create_shift_normal_user(self):
        self.client.login(username=self.normal_user.username, password="password")
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        response = self.client.post(
            reverse("v1:shifts_listcreate"),
            {
                "venue": self.order_venue.pk,
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T12:00:00.000Z",
                "can_order": True,
                "finalized": False,
                "max_orders_per_user": 2,
                "max_orders_total": 70,
                "assignees": [self.user_with_permissions.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_create_shift(self):
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        Shift.objects.all().delete()
        response = self.client.post(
            reverse("v1:shifts_listcreate"),
            {
                "venue": self.order_venue.pk,
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T12:00:00.000Z",
                "can_order": True,
                "finalized": False,
                "max_orders_per_user": 2,
                "max_orders_total": 70,
                "assignees": [self.user_with_permissions.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Shift.objects.all().count(), 1)
        shift = Shift.objects.first()
        self.assertEqual(shift.venue, self.order_venue)
        self.assertEqual(
            shift.start, timezone.datetime(year=2023, month=3, day=9, hour=10, tzinfo=datetime.timezone.utc)
        )
        self.assertEqual(
            shift.end, timezone.datetime(year=2023, month=3, day=9, hour=12, tzinfo=datetime.timezone.utc)
        )
        self.assertTrue(shift.can_order)
        self.assertFalse(shift.finalized)
        self.assertEqual(shift.max_orders_per_user, 2)
        self.assertEqual(shift.max_orders_total, 70)
        self.assertEqual(shift.assignees.all().count(), 1)
        self.assertEqual(shift.assignees.first(), self.user_with_permissions)

    @freeze_time("2023-03-09T13:00:00", tz_offset=1)
    def test_create_shift_finalized(self):
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        Shift.objects.all().delete()
        response = self.client.post(
            reverse("v1:shifts_listcreate"),
            {
                "venue": self.order_venue.pk,
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T15:00:00.000Z",
                "can_order": True,
                "finalized": True,
                "max_orders_per_user": 2,
                "max_orders_total": 70,
                "assignees": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Shift.objects.all().count(), 1)
        shift = Shift.objects.first()
        self.assertEqual(
            shift.end, timezone.datetime(year=2023, month=3, day=9, hour=13, tzinfo=datetime.timezone.utc)
        )

    def test_retrieve_shift(self):
        with self.subTest("Not logged in"):
            response = self.client.get(reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}))
            self.assertEqual(response.status_code, 403)

        with self.subTest("Logged in"):
            self.client.login(username=self.normal_user.username, password="password")
            response = self.client.get(reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}))
            self.assertEqual(response.status_code, 200)

    def test_full_update_shift_not_logged_in(self):
        response = self.client.put(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T15:00:00.000Z",
                "can_order": True,
                "finalized": True,
                "max_orders_per_user": 2,
                "max_orders_total": 70,
                "assignees": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_full_update_shift_normal_user(self):
        self.client.login(username=self.normal_user.username, password="password")
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        response = self.client.put(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T15:00:00.000Z",
                "can_order": True,
                "finalized": False,
                "max_orders_per_user": 2,
                "max_orders_total": 70,
                "assignees": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_full_update_shift(self):
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        response = self.client.put(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T15:00:00.000Z",
                "can_order": False,
                "finalized": False,
                "max_orders_per_user": 18,
                "max_orders_total": 50,
                "assignees": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        shift = Shift.objects.get(pk=self.shift.pk)
        self.assertEqual(
            shift.start, timezone.datetime(year=2023, month=3, day=9, hour=10, tzinfo=datetime.timezone.utc)
        )
        self.assertEqual(
            shift.end, timezone.datetime(year=2023, month=3, day=9, hour=15, tzinfo=datetime.timezone.utc)
        )
        self.assertFalse(shift.can_order)
        self.assertFalse(shift.finalized)
        self.assertEqual(shift.max_orders_per_user, 18)
        self.assertEqual(shift.max_orders_total, 50)
        self.assertEqual(shift.assignees.all().count(), 0)

    def test_full_update_shift_venue_not_updated(self):
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        test_venue = Venue.objects.create(name="Extra venue", slug="extra_venue")
        test_order_venue = OrderVenue.objects.create(venue=test_venue)
        response = self.client.put(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "venue": test_order_venue.pk,
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T15:00:00.000Z",
                "can_order": False,
                "finalized": False,
                "max_orders_per_user": 18,
                "max_orders_total": 50,
                "assignees": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        shift = Shift.objects.get(pk=self.shift.pk)
        self.assertEqual(shift.venue, self.order_venue)

    def test_partial_update_shift_not_logged_in(self):
        """A non-logged in use should not be able to use PATCH on a Shift."""
        response = self.client.patch(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "can_order": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_partial_update_shift_normal_user(self):
        """A normal user should not be able to use PATCH on a Shift."""
        self.client.login(username=self.normal_user.username, password="password")
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        response = self.client.patch(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "can_order": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_partial_update_shift(self):
        """Test PATCH update of Shift properties."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))

        with self.subTest("Start"):
            response = self.client.patch(
                reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
                {
                    "start": "2023-03-09T10:00:00.000Z",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            shift = Shift.objects.get(pk=self.shift.pk)
            self.assertEqual(
                shift.start, timezone.datetime(year=2023, month=3, day=9, hour=10, tzinfo=datetime.timezone.utc)
            )

        with self.subTest("End"):
            response = self.client.patch(
                reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
                {
                    "end": "2023-03-09T15:00:00.000Z",
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            shift = Shift.objects.get(pk=self.shift.pk)
            self.assertEqual(
                shift.end, timezone.datetime(year=2023, month=3, day=9, hour=15, tzinfo=datetime.timezone.utc)
            )

        with self.subTest("Can order"):
            response = self.client.patch(
                reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
                {
                    "can_order": False,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            shift = Shift.objects.get(pk=self.shift.pk)
            self.assertFalse(shift.can_order)

        with self.subTest("Max orders total"):
            response = self.client.patch(
                reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
                {
                    "max_orders_total": 100,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            shift = Shift.objects.get(pk=self.shift.pk)
            self.assertEqual(shift.max_orders_total, 100)

        with self.subTest("Max orders user"):
            response = self.client.patch(
                reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
                {
                    "max_orders_per_user": 50,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            shift = Shift.objects.get(pk=self.shift.pk)
            self.assertEqual(shift.max_orders_per_user, 50)

        with self.subTest("Assignees"):
            response = self.client.patch(
                reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
                {
                    "assignees": [],
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            shift = Shift.objects.get(pk=self.shift.pk)
            self.assertEqual(shift.assignees.all().count(), 0)

    def test_partial_update_shift_venue(self):
        """Updating a Shift venue should not be possible."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        test_venue = Venue.objects.create(name="Extra venue", slug="extra_venue")
        test_order_venue = OrderVenue.objects.create(venue=test_venue)
        response = self.client.patch(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {"venue": test_order_venue.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        shift = Shift.objects.get(pk=self.shift.pk)
        self.assertEqual(shift.venue, self.order_venue)

    @freeze_time("2023-03-09T13:00:00", tz_offset=1)
    def test_partial_update_shift_make_finalized(self):
        """Finalize a shift with PATCH."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        self.shift.start = timezone.datetime(year=2023, month=3, day=9, hour=10, tzinfo=datetime.timezone.utc)
        self.shift.end = timezone.datetime(year=2023, month=3, day=9, hour=16, tzinfo=datetime.timezone.utc)
        self.shift.save()
        response = self.client.patch(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "finalized": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        shift = Shift.objects.get(pk=self.shift.pk)
        self.assertTrue(shift.finalized)
        self.assertEqual(
            shift.end, timezone.datetime(year=2023, month=3, day=9, hour=13, tzinfo=datetime.timezone.utc)
        )
        self.assertFalse(shift.can_order)

    def test_partial_update_shift_make_finalized_orders_not_ready(self):
        """Finalizing a Shift where some orders are not ready or paid yet should fail."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        Order.objects.create(product=self.product, shift=self.shift, user=self.normal_user)
        response = self.client.patch(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "finalized": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_partial_update_shift_unfinalize(self):
        """A Shift can never be unfinalized."""
        self.client.login(username=self.user_with_permissions.username, password="password")
        self.assertTrue(self.user_with_permissions.has_perm("orders.can_manage_shift_in_venue", self.order_venue))
        self.shift.finalized = True
        self.shift.save()
        response = self.client.patch(
            reverse("v1:shift_retrieveupdate", kwargs={"pk": self.shift.pk}),
            {
                "finalized": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
