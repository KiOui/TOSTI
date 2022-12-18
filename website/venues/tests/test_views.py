from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from associations.models import Association
from venues import models
from venues.models import Venue

User = get_user_model()


class VenueViewTests(TestCase):

    fixtures = ["users.json", "associations.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(pk=2)
        cls.user.set_password("password")
        cls.user.save()

    def test_venue_calendar_view(self):
        response = self.client.get(reverse("venues:calendar"))
        self.assertEqual(response.status_code, 200)

    def test_request_reservation_view_get(self):
        self.assertTrue(self.client.login(username=self.user.username, password="password"))
        response = self.client.get(reverse("venues:add_reservation"))
        self.assertEqual(response.status_code, 200)

    def test_request_reservation_view_get_not_logged_in(self):
        response = self.client.get(reverse("venues:add_reservation"), follow=False)
        self.assertEqual(response.status_code, 302)

    @freeze_time()
    def test_request_reservation_view_post(self):
        self.assertTrue(self.client.login(username=self.user.username, password="password"))
        reservation_pks_before_post = [x.pk for x in models.Reservation.objects.all()]
        now = timezone.localtime(timezone.now())
        response = self.client.post(
            reverse("venues:add_reservation"),
            data={
                "venue": 1,
                "association": 1,
                "start": (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
                "end": (now + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M"),
                "title": "Test reservation",
                "comment": "We will be serving special beer",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        reservation_pks_after_post = [x.pk for x in models.Reservation.objects.all()]
        reservations_created = list(set(reservation_pks_after_post).difference(set(reservation_pks_before_post)))
        self.assertEqual(len(reservations_created), 1)
        reservation_created = models.Reservation.objects.get(pk=reservations_created[0])
        self.assertEqual(reservation_created.title, "Test reservation")

    def test_request_reservation_view_post_not_logged_in(self):
        now = timezone.localtime(timezone.now())
        response = self.client.post(
            reverse("venues:add_reservation"),
            data={
                "venue": 1,
                "association": 1,
                "start": (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
                "end": (now + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M"),
                "title": "Test reservation",
                "comment": "We will be serving special beer",
            },
            follow=False,
        )
        self.assertEqual(response.status_code, 302)

    def test_list_reservations_view(self):
        self.assertTrue(self.client.login(username=self.user.username, password="password"))
        models.Reservation.objects.create(
            title="Test reservation",
            user_created=self.user,
            association=Association.objects.get(pk=1),
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=5),
            venue=Venue.objects.get(pk=1),
            comment="Test comment",
            accepted=None,
        )
        models.Reservation.objects.create(
            title="Test reservation denied",
            user_created=self.user,
            association=Association.objects.get(pk=1),
            start=timezone.now() + timedelta(days=1),
            end=timezone.now() + timedelta(days=1, hours=5),
            venue=Venue.objects.get(pk=1),
            comment="Test comment",
            accepted=False,
        )

        models.Reservation.objects.create(
            title="Test reservation accepted",
            user_created=self.user,
            association=Association.objects.get(pk=1),
            start=timezone.now() + timedelta(days=2),
            end=timezone.now() + timedelta(days=2, hours=5),
            venue=Venue.objects.get(pk=1),
            comment="Test comment",
            accepted=True,
        )
        response = self.client.get(reverse("venues:list_reservations"))
        self.assertEqual(response.status_code, 200)

    def test_reservations_list_view_not_logged_in(self):
        response = self.client.get(reverse("venues:list_reservations"), follow=False)
        self.assertEqual(response.status_code, 302)
