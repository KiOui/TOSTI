import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from django.utils import timezone
from guardian.shortcuts import assign_perm

from orders.models import Shift, OrderVenue
from orders.services import add_user_to_assignees_of_shift, user_is_blacklisted
from venues.models import Venue


User = get_user_model()
logging.disable()


class OrderViewTests(TestCase):

    fixtures = ["users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        venue_pk_1 = Venue.objects.get(pk=1)
        order_venue_1 = OrderVenue.objects.create(venue=venue_pk_1)
        cls.order_venue_1 = order_venue_1
        venue_pk_2 = Venue.objects.get(pk=2)
        cls.order_venue_2 = OrderVenue.objects.create(venue=venue_pk_2)
        cls.shift = Shift.objects.create(
            venue=order_venue_1, start=timezone.now(), end=timezone.now() + timedelta(hours=4)
        )
        cls.normal_user = User.objects.get(pk=2)

    def setUp(self):
        self.normal_user.set_password("temporary")
        self.normal_user.save()

    def test_create_shift_view(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        response = self.client.get(reverse("orders:shift_create", kwargs={"venue": self.order_venue_1}), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_create_shift_view_not_logged_in(self):
        response = self.client.get(reverse("orders:shift_create", kwargs={"venue": self.order_venue_1}), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_create_shift_view_no_permissions(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        response = self.client.get(reverse("orders:shift_create", kwargs={"venue": self.order_venue_1}), follow=True)
        self.assertEqual(response.status_code, 403)

    def test_create_shift_view_post(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_2)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_2))
        self.assertFalse(Shift.objects.filter(venue=self.order_venue_2).exists())
        response = self.client.post(
            reverse("orders:shift_create", kwargs={"venue": self.order_venue_2}),
            follow=True,
            data={
                "venue": self.order_venue_2.pk,
                "start": timezone.now(),
                "end": timezone.now() + timedelta(hours=4),
            },
        )
        self.assertTrue(Shift.objects.filter(venue=self.order_venue_2).exists())
        self.assertEqual(response.status_code, 200)

    def test_create_shift_view_post_no_permissions(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_2))
        self.assertFalse(Shift.objects.filter(venue=self.order_venue_2).exists())
        response = self.client.post(
            reverse("orders:shift_create", kwargs={"venue": self.order_venue_1}),
            follow=True,
            data={
                "venue": self.order_venue_2.pk,
                "start": timezone.now(),
                "end": timezone.now() + timedelta(hours=4),
            },
        )
        self.assertFalse(Shift.objects.filter(venue=self.order_venue_2).exists())
        self.assertEqual(response.status_code, 200)

    def test_shift_view(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        self.assertFalse(user_is_blacklisted(self.normal_user))
        response = self.client.get(reverse("orders:shift_overview", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 200)

    def test_join_shift_view(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        response = self.client.get(reverse("orders:shift_join", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 200)

    def test_join_shift_view_not_logged_in(self):
        response = self.client.get(reverse("orders:shift_join", kwargs={"shift": self.shift}), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_join_shift_view_no_permissions(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        response = self.client.get(reverse("orders:shift_join", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 403)

    def test_join_shift_view_already_joined(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        add_user_to_assignees_of_shift(self.normal_user, self.shift)
        response = self.client.get(reverse("orders:shift_join", kwargs={"shift": self.shift}))
        self.assertRedirects(response, reverse("orders:shift_admin", kwargs={"shift": self.shift}))

    def test_join_shift_view_post(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        self.assertFalse(self.normal_user in self.shift.assignees.all())
        response = self.client.post(
            reverse("orders:shift_join", kwargs={"shift": self.shift}), data={"confirm": "Yes"}
        )
        self.assertRedirects(response, reverse("orders:shift_admin", kwargs={"shift": self.shift}))
        self.assertTrue(self.normal_user in self.shift.assignees.all())

    def test_join_shift_view_post_no(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        self.assertFalse(self.normal_user in self.shift.assignees.all())
        response = self.client.post(reverse("orders:shift_join", kwargs={"shift": self.shift}), data={"confirm": "No"})
        self.assertRedirects(response, reverse("index"))
        self.assertFalse(self.normal_user in self.shift.assignees.all())

    def test_join_shift_view_post_no_data(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        self.assertFalse(self.normal_user in self.shift.assignees.all())
        response = self.client.post(reverse("orders:shift_join", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.normal_user in self.shift.assignees.all())

    def test_shift_admin_view(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        add_user_to_assignees_of_shift(self.normal_user, self.shift)
        response = self.client.get(reverse("orders:shift_admin", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 200)

    def test_shift_admin_view_not_in_assignees(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        assign_perm("orders.can_manage_shift_in_venue", self.normal_user, self.order_venue_1)
        self.assertTrue(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        response = self.client.get(reverse("orders:shift_admin", kwargs={"shift": self.shift}))
        self.assertRedirects(response, reverse("orders:shift_join", kwargs={"shift": self.shift}))

    def test_shift_admin_view_no_permissions(self):
        self.assertTrue(self.client.login(username=self.normal_user.username, password="temporary"))
        self.assertFalse(self.normal_user.has_perm("orders.can_manage_shift_in_venue", self.order_venue_1))
        response = self.client.get(reverse("orders:shift_admin", kwargs={"shift": self.shift}))
        self.assertEqual(response.status_code, 302)
