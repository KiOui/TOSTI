import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from rest_framework.test import APITestCase

from associations.models import Association
from venues.models import Venue, Reservation

User = get_user_model()
logging.disable()


class VenuesAPITests(APITestCase):
    fixtures = ["associations.json", "users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        cls.venue = Venue.objects.get(pk=1)
        cls.association = Association.objects.get(pk=1)
        cls.normal_user = User.objects.get(pk=2)
        cls.normal_user.set_password("password")
        cls.normal_user.save()
        cls.reservation = Reservation.objects.create(
            title="Test reservation",
            association=cls.association,
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=1, hours=4),
            venue=cls.venue,
            user_created=cls.normal_user,
            comments="Test comments",
        )

    def test_list_venues_not_logged_in(self):
        """Listing venues while not logged in."""
        response = self.client.get(reverse("v1:venue_list"))
        self.assertEqual(response.status_code, 200)

    def test_get_venue_not_logged_in(self):
        """GET a venue while not logged in."""
        response = self.client.get(
            reverse("v1:venue_retrieve", kwargs={"pk": self.venue.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_get_reservations_not_logged_in(self):
        """Non-logged in users should be able to list reservations."""
        response = self.client.get(reverse("v1:reservations_listcreate"))
        self.assertEqual(response.status_code, 200)

    def test_add_reservation_not_logged_in(self):
        """Non-logged in users should not be able to add a reservation."""

        now = timezone.now()

        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": (now + timedelta(hours=5)).isoformat(),
                "end": (now + timedelta(hours=12)).isoformat(),
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_add_reservation(self):
        """Non-logged in users should not be able to add a reservation."""
        self.client.login(username=self.normal_user.username, password="password")
        Reservation.objects.all().delete()

        now = timezone.now()

        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": (now + timedelta(hours=5)).isoformat(),
                "end": (now + timedelta(hours=12)).isoformat(),
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reservation.objects.all().count(), 1)
        reservation = Reservation.objects.first()
        self.assertEqual(reservation.venue.pk, self.venue.pk)
        self.assertEqual(reservation.association.pk, 1)
        self.assertEqual(reservation.user_created, self.normal_user)

    def test_add_reservation_start_after_end(self):
        """Non-logged in users should not be able to add a reservation."""
        self.client.login(username=self.normal_user.username, password="password")
        Reservation.objects.all().delete()

        now = timezone.now()

        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": (now + timedelta(hours=12)).isoformat(),
                "end": (now + timedelta(hours=5)).isoformat(),
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_add_reservation_venue_not_reservable(self):
        """Non-logged in users should not be able to add a reservation."""
        self.client.login(username=self.normal_user.username, password="password")
        Reservation.objects.all().delete()

        now = timezone.now()

        self.venue.can_be_reserved = False
        self.venue.save()

        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": (now + timedelta(hours=5)).isoformat(),
                "end": (now + timedelta(hours=12)).isoformat(),
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 400)

    @freeze_time()
    def test_reservation_start_before_now(self):
        self.client.login(username=self.normal_user.username, password="password")
        now = timezone.now()
        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": (now - timedelta(hours=5)).isoformat(),
                "end": (now + timedelta(hours=1)).isoformat(),
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 400)

    @freeze_time()
    def test_reservation_overlapping_accepted_reservation(self):
        self.client.login(username=self.normal_user.username, password="password")
        Reservation.objects.all().delete()

        now = timezone.now()
        Reservation.objects.create(
            title="Test reservation",
            start=now + timedelta(hours=5),
            end=now + timedelta(hours=11),
            venue=self.venue,
            accepted=True,
        )

        with self.subTest("Overlapping end"):
            response = self.client.post(
                reverse("v1:reservations_listcreate"),
                {
                    "venue": self.venue,
                    "association": self.association,
                    "start": (now + timedelta(hours=3)).isoformat(),
                    "end": (now + timedelta(hours=7)).isoformat(),
                    "title": "Test reservation overlapping end",
                },
            )
            self.assertEqual(response.status_code, 400)

        with self.subTest("Overlapping start"):
            response = self.client.post(
                reverse("v1:reservations_listcreate"),
                {
                    "venue": self.venue,
                    "association": self.association,
                    "start": (now + timedelta(hours=8)).isoformat(),
                    "end": (now + timedelta(hours=15)).isoformat(),
                    "title": "Test reservation overlapping end",
                },
            )
            self.assertEqual(response.status_code, 400)

        with self.subTest("Reservation inside already created reservation"):
            response = self.client.post(
                reverse("v1:reservations_listcreate"),
                {
                    "venue": self.venue,
                    "association": self.association,
                    "start": (now + timedelta(hours=6)).isoformat(),
                    "end": (now + timedelta(hours=10)).isoformat(),
                    "title": "Test reservation overlapping end",
                },
            )
            self.assertEqual(response.status_code, 400)

        with self.subTest(
            "Reservation completely overlapping already created reservation"
        ):
            response = self.client.post(
                reverse("v1:reservations_listcreate"),
                {
                    "venue": self.venue,
                    "association": self.association,
                    "start": (now + timedelta(hours=3)).isoformat(),
                    "end": (now + timedelta(hours=13)).isoformat(),
                    "title": "Test reservation overlapping end",
                },
            )
            self.assertEqual(response.status_code, 400)
