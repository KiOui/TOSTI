from datetime import datetime
import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse

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
            start=datetime.now() + timedelta(days=1),
            end=datetime.now() + timedelta(days=1, hours=4),
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
        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T12:00:00.000Z",
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_add_reservation(self):
        """Non-logged in users should not be able to add a reservation."""
        self.client.login(username=self.normal_user.username, password="password")
        Reservation.objects.all().delete()
        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": "2023-03-09T10:00:00.000Z",
                "end": "2023-03-09T12:00:00.000Z",
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
        response = self.client.post(
            reverse("v1:reservations_listcreate"),
            {
                "venue": self.venue.pk,
                "start": "2023-03-09T12:00:00.000Z",
                "end": "2023-03-09T09:00:00.000Z",
                "title": "Test title",
                "association": 1,
            },
        )
        self.assertEqual(response.status_code, 400)
