from datetime import timedelta

import freezegun
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from orders.models import OrderVenue, Shift
from venues.models import Venue


class TostiViewTests(TestCase):
    fixtures = ["venues.json"]

    def test_index_view(self):
        with freezegun.freeze_time(timezone.now()):
            venue_pk_1 = Venue.objects.get(pk=1)
            order_venue_1 = OrderVenue.objects.create(venue=venue_pk_1)
            venue_pk_2 = Venue.objects.get(pk=2)
            OrderVenue.objects.create(venue=venue_pk_2)
            Shift.objects.create(venue=order_venue_1, start=timezone.now(), end=timezone.now() + timedelta(hours=4))
            response = self.client.get(reverse("index"))
            self.assertEqual(response.status_code, 200)

    def test_privacy_view(self):
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)

    def test_documentation_view(self):
        response = self.client.get(reverse("documentation"))
        self.assertEqual(response.status_code, 200)
