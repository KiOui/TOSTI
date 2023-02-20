from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from associations.models import Association
from venues import models
from venues import forms

User = get_user_model()


class VenuesFormsTests(TestCase):
    fixtures = ["associations.json", "users.json", "venues.json"]

    @classmethod
    def setUpTestData(cls):
        cls.venue = models.Venue.objects.get(pk=1)
        cls.association = Association.objects.get(pk=1)

    @freeze_time()
    def test_reservation_form(self):
        now = timezone.now()
        form_data = {
            "venue": self.venue,
            "association": self.association,
            "start": now + timedelta(hours=1),
            "end": now + timedelta(hours=5),
            "title": "Test reservation",
        }
        form = forms.ReservationForm(form_data)
        self.assertTrue(form.is_valid())
        reservation = form.save()
        reservation.accepted = True
        reservation.save()
        form_data_2 = {
            "venue": self.venue,
            "association": self.association,
            "start": now + timedelta(hours=6),
            "end": now + timedelta(hours=11),
            "title": "Test reservation 2",
        }
        form_2 = forms.ReservationForm(form_data_2)
        self.assertTrue(form_2.is_valid())

    @freeze_time()
    def test_reservation_end_before_start(self):
        now = timezone.now()
        form_data = {
            "venue": self.venue,
            "association": self.association,
            "start": now + timedelta(hours=5),
            "end": now + timedelta(hours=1),
            "title": "Test reservation",
        }
        form = forms.ReservationForm(form_data)
        self.assertFalse(form.is_valid())

    @freeze_time()
    def test_reservation_start_before_now(self):
        now = timezone.now()
        form_data = {
            "venue": self.venue,
            "association": self.association,
            "start": now - timedelta(hours=5),
            "end": now + timedelta(hours=1),
            "title": "Test reservation",
        }
        form = forms.ReservationForm(form_data)
        self.assertFalse(form.is_valid())

    @freeze_time()
    def test_reservation_overlapping_accepted_reservation(self):
        now = timezone.now()
        models.Reservation.objects.create(
            title="Test reservation",
            start=now + timedelta(hours=5),
            end=now + timedelta(hours=11),
            venue=self.venue,
            accepted=True,
        )

        with self.subTest("Overlapping end"):
            form_data = {
                "venue": self.venue,
                "association": self.association,
                "start": now + timedelta(hours=3),
                "end": now + timedelta(hours=7),
                "title": "Test reservation overlapping end",
            }
            form = forms.ReservationForm(form_data)
            self.assertFalse(form.is_valid())

        with self.subTest("Overlapping start"):
            form_data = {
                "venue": self.venue,
                "association": self.association,
                "start": now + timedelta(hours=8),
                "end": now + timedelta(hours=15),
                "title": "Test reservation overlapping start",
            }
            form = forms.ReservationForm(form_data)
            self.assertFalse(form.is_valid())

        with self.subTest("Reservation inside already created reservation"):
            form_data = {
                "venue": self.venue,
                "association": self.association,
                "start": now + timedelta(hours=6),
                "end": now + timedelta(hours=10),
                "title": "Test reservation inside already created reservation",
            }
            form = forms.ReservationForm(form_data)
            self.assertFalse(form.is_valid())

        with self.subTest("Reservation completely overlapping already created reservation"):
            form_data = {
                "venue": self.venue,
                "association": self.association,
                "start": now + timedelta(hours=3),
                "end": now + timedelta(hours=13),
                "title": "Test reservation completely overlapping already created reservation",
            }
            form = forms.ReservationForm(form_data)
            self.assertFalse(form.is_valid())
