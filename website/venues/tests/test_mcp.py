"""Tests for the venues app's MCP toolset."""

from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from venues.mcp import VenueTools
from venues.models import Reservation, Venue

User = get_user_model()


class _StubRequest:
    def __init__(self, user, auth=None):
        self.user = user
        self.auth = auth


class VenueToolsListTests(TestCase):
    fixtures = ["venues.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="x")
        self.tools = VenueTools(request=_StubRequest(self.user))

    def test_list_venues_returns_all_venues(self):
        result = self.tools.list_venues()
        self.assertEqual(len(result), Venue.objects.count())
        slugs = {v["slug"] for v in result}
        self.assertIn("noordkantine", slugs)


class VenueToolsCreateReservationTests(TestCase):
    fixtures = ["venues.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="reserver", password="x")
        self.venue = Venue.objects.first()

    def test_unknown_venue_returns_error(self):
        tools = VenueTools(request=_StubRequest(self.user))
        result = tools.create_venue_reservation(
            venue_slug="nonexistent",
            title="Foo",
            start="2030-01-01T10:00:00+00:00",
            end="2030-01-01T11:00:00+00:00",
        )
        self.assertIn("error", result)

    def test_invalid_dates_return_error(self):
        tools = VenueTools(request=_StubRequest(self.user))
        result = tools.create_venue_reservation(
            venue_slug=self.venue.slug,
            title="Foo",
            start="not-a-date",
            end="also-not",
        )
        self.assertIn("error", result)

    def test_end_before_start_returns_error(self):
        tools = VenueTools(request=_StubRequest(self.user))
        result = tools.create_venue_reservation(
            venue_slug=self.venue.slug,
            title="Foo",
            start="2030-01-01T11:00:00+00:00",
            end="2030-01-01T10:00:00+00:00",
        )
        self.assertIn("error", result)

    def test_successful_reservation_persists(self):
        tools = VenueTools(request=_StubRequest(self.user))
        result = tools.create_venue_reservation(
            venue_slug=self.venue.slug,
            title="Birthday party",
            start="2030-01-01T10:00:00+00:00",
            end="2030-01-01T12:00:00+00:00",
            comments="cake",
        )
        self.assertNotIn("error", result)
        reservation = Reservation.objects.get(pk=result["reservation_id"])
        self.assertEqual(reservation.user_created, self.user)
        self.assertEqual(reservation.venue, self.venue)
        self.assertEqual(reservation.title, "Birthday party")
        self.assertIsNone(reservation.accepted)

    def test_token_without_write_scope_is_rejected(self):
        token = MagicMock()
        token.is_valid = MagicMock(return_value=False)
        tools = VenueTools(request=_StubRequest(self.user, auth=token))
        result = tools.create_venue_reservation(
            venue_slug=self.venue.slug,
            title="Blocked",
            start="2030-01-01T10:00:00+00:00",
            end="2030-01-01T11:00:00+00:00",
        )
        self.assertIn("error", result)
        self.assertIn("write", result["error"])
        self.assertEqual(Reservation.objects.count(), 0)
