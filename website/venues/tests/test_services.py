from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from associations.models import Association
from venues import services
from venues.models import Venue

User = get_user_model()


class VenueServicesTests(TestCase):

    fixtures = ["associations.json", "users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.get(pk=1)
        cls.user.profile.association = Association.objects.get(pk=1)
        cls.user.save()
        cls.venue_1 = Venue.objects.get(pk=1)
        cls.venue_2 = Venue.objects.get(pk=2)

    @freeze_time()
    def test_add_reservation(self):
        with self.subTest("Add reservation"):
            reservation_added = services.add_reservation(
                self.user,
                self.venue_1,
                timezone.now() + timedelta(hours=3),
                timezone.now() + timedelta(hours=5),
                "Test reservation 1",
            )
            self.assertEqual(reservation_added.association, Association.objects.get(pk=1))

        with self.subTest("Add reservation after another reservation"):
            services.add_reservation(
                self.user,
                self.venue_1,
                timezone.now() + timedelta(hours=7),
                timezone.now() + timedelta(hours=9),
                "Test reservation 2 same venue",
            )

        with self.subTest("Add reservation before another reservation"):
            services.add_reservation(
                self.user,
                self.venue_1,
                timezone.now() + timedelta(hours=1),
                timezone.now() + timedelta(hours=2),
                "Test reservation 3",
            )

        with self.subTest("Add reservation for other venue overlapping"):
            services.add_reservation(
                self.user,
                self.venue_2,
                timezone.now() + timedelta(hours=3),
                timezone.now() + timedelta(hours=5),
                "Test reservation 4",
            )

    @freeze_time()
    def test_add_reservation_end_before_start(self):
        self.assertRaises(
            ValueError,
            services.add_reservation,
            self.user,
            self.venue_2,
            timezone.now() + timedelta(hours=5),
            timezone.now() + timedelta(hours=3),
            "Test reservation",
        )

    @freeze_time()
    def test_add_reservation_start_in_past(self):
        self.assertRaises(
            ValueError,
            services.add_reservation,
            self.user,
            self.venue_2,
            timezone.now() - timedelta(hours=5),
            timezone.now() - timedelta(hours=3),
            "Test reservation",
        )

    def test_add_overlapping_reservation(self):
        reservation = services.add_reservation(
            self.user,
            self.venue_1,
            timezone.now() + timedelta(hours=3),
            timezone.now() + timedelta(hours=5),
            "Test reservation 1",
        )
        reservation.accepted = True
        reservation.save()
        self.assertRaises(
            ValueError,
            services.add_reservation,
            self.user,
            self.venue_1,
            timezone.now() + timedelta(hours=2),
            timezone.now() + timedelta(hours=4),
            "Test reservation 2",
        )
