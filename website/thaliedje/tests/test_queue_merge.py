"""Tests for the merged queue observer + enricher.

These cover the state machine that turns Spotify's live queue plus our
``SpotifyQueueItem`` request log into a single annotated view:

* ``observe_player_state`` walks ``player.queue`` + ``_current_playback``
  and updates ``observed_at_position`` / ``played_at`` on the request log.
* ``enrich_spotify_queue`` joins the live queue back to the request log
  using the pinned position first, falling back to oldest-unmatched when
  the observer hasn't pinned anything yet.
"""

from datetime import timedelta
from unittest.mock import PropertyMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from thaliedje.models import SpotifyPlayer, SpotifyQueueItem, SpotifyTrack
from thaliedje.services import enrich_spotify_queue, observe_player_state
from venues.models import Venue

User = get_user_model()


def _track(track_id, name="Song"):
    return SpotifyTrack.objects.create(track_id=track_id, track_name=name)


def _queue_entry(track_id, name=None):
    return {
        "track_id": track_id,
        "track_name": name or f"Song {track_id}",
        "track_artists": [],
        "duration_ms": 1000,
    }


def _patched_player_state(player, queue_snapshot, currently_playing_id=None):
    """Mock ``player.queue`` and ``_current_playback`` for one call."""
    playback = {"item": {"id": currently_playing_id}} if currently_playing_id else None
    return patch.multiple(
        SpotifyPlayer,
        queue=PropertyMock(return_value=queue_snapshot),
        _current_playback=PropertyMock(return_value=playback),
    )


class _PlayerSetupMixin:
    """Real SpotifyPlayer rows so FKs and ``isinstance`` checks pass."""

    fixtures = ["venues.json"]

    @classmethod
    def setUpTestData(cls):
        cls.venue = Venue.objects.first()
        cls.player = SpotifyPlayer.objects.create(
            slug="canteen-test",
            venue=cls.venue,
            client_id="ci",
            client_secret="cs",
            redirect_uri="https://example.com/cb",
            playback_device_id="dev-1",
        )
        cls.alice = User.objects.create_user(username="alice", password="x")
        cls.bob = User.objects.create_user(username="bob", password="x")


class ObservePlayerStateTests(_PlayerSetupMixin, TestCase):
    """``observe_player_state`` updates the request log to match reality."""

    def test_pins_position_on_first_observation(self):
        track = _track("aaa")
        row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            observe_player_state(self.player)
        row.refresh_from_db()
        self.assertEqual(row.observed_at_position, 0)
        self.assertIsNone(row.played_at)

    def test_advances_position_as_queue_moves(self):
        track = _track("aaa")
        row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        # First the request is at position 2.
        with _patched_player_state(
            self.player,
            [_queue_entry("xxx"), _queue_entry("yyy"), _queue_entry("aaa")],
        ):
            observe_player_state(self.player)
        row.refresh_from_db()
        self.assertEqual(row.observed_at_position, 2)
        # Then the queue advances and the request is now at position 0.
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            observe_player_state(self.player)
        row.refresh_from_db()
        self.assertEqual(row.observed_at_position, 0)
        self.assertIsNone(row.played_at)

    def test_marks_played_when_track_leaves_queue(self):
        track = _track("aaa")
        row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        # Seen once at position 0.
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            observe_player_state(self.player)
        # Next poll: queue is empty and the track isn't currently playing
        # either — Spotify advanced past it (or it got skipped).
        with _patched_player_state(self.player, []):
            observe_player_state(self.player)
        row.refresh_from_db()
        self.assertIsNotNone(row.played_at)
        self.assertEqual(row.observed_at_position, 0)

    def test_does_not_mark_played_while_currently_playing(self):
        """The track moved from the queue to "currently playing" — not gone yet."""
        track = _track("aaa")
        row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            observe_player_state(self.player)
        # Now queue empty, but the track IS currently playing.
        with _patched_player_state(self.player, [], currently_playing_id="aaa"):
            observe_player_state(self.player)
        row.refresh_from_db()
        self.assertIsNone(row.played_at)

    def test_two_requests_for_same_track_get_distinct_positions(self):
        track = _track("aaa")
        alice_row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        bob_row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.bob
        )
        with _patched_player_state(
            self.player, [_queue_entry("aaa"), _queue_entry("aaa")]
        ):
            observe_player_state(self.player)
        alice_row.refresh_from_db()
        bob_row.refresh_from_db()
        # Alice requested first (oldest unclaimed); she gets position 0.
        self.assertEqual(alice_row.observed_at_position, 0)
        self.assertEqual(bob_row.observed_at_position, 1)

    def test_request_for_track_not_in_queue_is_marked_played(self):
        """The operator queued the same track outside TOSTI and absorbed our slot."""
        track = _track("aaa")
        row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        # Queue contains only OTHER tracks; our request never matched.
        with _patched_player_state(self.player, [_queue_entry("zzz")]):
            observe_player_state(self.player)
        row.refresh_from_db()
        # Honest unknown — we mark it played to keep the working set bounded.
        self.assertIsNotNone(row.played_at)

    def test_unavailable_queue_is_a_noop(self):
        track = _track("aaa")
        row = SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        with _patched_player_state(self.player, None):
            result = observe_player_state(self.player)
        self.assertEqual(result, {"skipped": "queue_unavailable"})
        row.refresh_from_db()
        self.assertIsNone(row.played_at)
        self.assertIsNone(row.observed_at_position)


class EnrichSpotifyQueueTests(_PlayerSetupMixin, TestCase):
    """``enrich_spotify_queue`` joins live queue with the request log."""

    def test_observed_position_pin_drives_attribution(self):
        track = _track("aaa")
        SpotifyQueueItem.objects.create(
            track=track,
            player=self.player,
            requested_by=self.alice,
            observed_at_position=0,
        )
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            result = enrich_spotify_queue(self.player)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["requested_by"]["username"], "alice")

    def test_two_requests_same_track_attributed_in_position_order(self):
        track = _track("aaa")
        SpotifyQueueItem.objects.create(
            track=track,
            player=self.player,
            requested_by=self.alice,
            observed_at_position=0,
        )
        SpotifyQueueItem.objects.create(
            track=track,
            player=self.player,
            requested_by=self.bob,
            observed_at_position=1,
        )
        with _patched_player_state(
            self.player, [_queue_entry("aaa"), _queue_entry("aaa")]
        ):
            result = enrich_spotify_queue(self.player)
        self.assertEqual(result[0]["requested_by"]["username"], "alice")
        self.assertEqual(result[1]["requested_by"]["username"], "bob")

    def test_unmatched_entry_is_left_unattributed(self):
        """Operator queued via Spotify directly — no DB row exists."""
        with _patched_player_state(self.player, [_queue_entry("zzz")]):
            result = enrich_spotify_queue(self.player)
        self.assertEqual(result[0]["requested_by"], None)
        self.assertEqual(result[0]["requested_at"], None)

    def test_fallback_to_oldest_when_position_not_pinned(self):
        """Before the observer has run: greedy match still attributes the entry."""
        track = _track("aaa")
        SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.alice
        )
        # Newer row that COULD also match — but the older one wins.
        SpotifyQueueItem.objects.create(
            track=track, player=self.player, requested_by=self.bob
        )
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            result = enrich_spotify_queue(self.player)
        self.assertEqual(result[0]["requested_by"]["username"], "alice")

    def test_played_rows_do_not_attribute(self):
        """A request already marked played must not steal a later entry."""
        track = _track("aaa")
        SpotifyQueueItem.objects.create(
            track=track,
            player=self.player,
            requested_by=self.alice,
            played_at=timezone.now() - timedelta(minutes=10),
        )
        # New queue entry for the same track — should NOT be attributed
        # to Alice (whose row already played).
        with _patched_player_state(self.player, [_queue_entry("aaa")]):
            result = enrich_spotify_queue(self.player)
        self.assertEqual(result[0]["requested_by"], None)

    def test_unavailable_queue_returns_none(self):
        with _patched_player_state(self.player, None):
            self.assertIsNone(enrich_spotify_queue(self.player))
