"""Tests for the thaliedje app's MCP toolset."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from thaliedje.mcp import ThaliedjeTools
from thaliedje.models import MarietjePlayer
from thaliedje.services import search_tracks as search_tracks_service
from venues.models import Venue

User = get_user_model()


class _StubRequest:
    def __init__(self, user, auth=None):
        self.user = user
        self.auth = auth


class ThaliedjeToolsReadTests(TestCase):
    fixtures = ["venues.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="reader", password="x")
        self.tools = ThaliedjeTools(request=_StubRequest(self.user))

    def test_get_player_state_unknown_venue_returns_error(self):
        result = self.tools.get_player_state("does-not-exist")
        self.assertIn("error", result)

    def test_get_player_state_returns_marietje_subclass_state(self):
        """Regression: bare ``Player.objects.get`` returns the base class,
        whose ``current_*`` properties raise ``NotImplementedError``.
        ``get_player_for_venue`` must use ``select_subclasses()`` so the
        MarietjePlayer-specific properties resolve.
        """
        venue = Venue.objects.first()
        MarietjePlayer.objects.create(slug="marietje-noord", venue=venue)
        with patch(
            "thaliedje.models.MarietjePlayer._current_playback", return_value=None
        ):
            result = self.tools.get_player_state(venue.slug)
        # No error key, and the keys we promise are present.
        self.assertNotIn("error", result)
        self.assertEqual(result["venue"], str(venue))
        self.assertIn("is_playing", result)
        self.assertIn("track", result)


class ThaliedjeToolsRequestSongTests(TestCase):
    fixtures = ["venues.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="requester", password="x")

    def test_unknown_venue_returns_error(self):
        tools = ThaliedjeTools(request=_StubRequest(self.user))
        result = tools.request_song(venue_slug="nonexistent", track_id="abc")
        self.assertIn("error", result)

    def test_request_song_calls_underlying_service(self):
        venue = Venue.objects.first()
        player = MarietjePlayer.objects.create(slug="test-player", venue=venue)

        tools = ThaliedjeTools(request=_StubRequest(self.user))
        with patch("thaliedje.mcp.request_song") as mock_service:
            queued = MagicMock()
            queued.track.track_name = "Test Track"
            mock_service.return_value = queued

            result = tools.request_song(venue_slug=venue.slug, track_id="track-id-42")

        mock_service.assert_called_once()
        args, _ = mock_service.call_args
        # The service uses select_subclasses(), so we get a concrete
        # MarietjePlayer back — not the base ``Player``.
        self.assertIsInstance(args[0], MarietjePlayer)
        self.assertEqual(args[0].pk, player.pk)
        self.assertEqual(args[1], self.user)
        self.assertEqual(args[2], "track-id-42")
        self.assertTrue(result["queued"])
        self.assertEqual(result["track"]["name"], "Test Track")

    def test_request_song_with_token_missing_scope_is_rejected(self):
        token = MagicMock()
        token.is_valid = MagicMock(return_value=False)
        tools = ThaliedjeTools(request=_StubRequest(self.user, auth=token))
        result = tools.request_song(venue_slug="any", track_id="t")
        self.assertIn("error", result)
        self.assertIn("thaliedje:request", result["error"])


class SearchTracksServiceTests(TestCase):
    """``search_tracks`` normalises the per-backend search() return shape.

    Regression for Sentry TOSTI-YP / TOSTI-YQ: ``SpotifyPlayer.search``
    returns ``{"tracks": [...]}`` (a dict), but the service iterated it
    as if it were a flat list of track dicts. Iterating a dict yields
    its string keys, so the first ``r.get("id")`` blew up with
    ``AttributeError: 'str' object has no attribute 'get'``.
    """

    def _player(self, raw):
        player = MagicMock()
        player.search.return_value = raw
        return player

    def test_unwraps_spotify_dict_shape(self):
        raw = {
            "tracks": [
                {"id": "1", "name": "Song A", "artists": ["Artist"]},
                {"id": "2", "name": "Song B", "artists": ["Artist 2"]},
            ],
            # other categories should be ignored by ``search_tracks``
            "albums": [{"id": "x", "name": "Album"}],
        }
        result = search_tracks_service(self._player(raw), "anything")
        self.assertEqual(
            result,
            [
                {"id": "1", "name": "Song A", "artists": ["Artist"]},
                {"id": "2", "name": "Song B", "artists": ["Artist 2"]},
            ],
        )

    def test_passes_through_flat_list_shape(self):
        raw = [{"id": "1", "name": "Song A", "artists": ["Artist"]}]
        self.assertEqual(
            search_tracks_service(self._player(raw), "anything"),
            [{"id": "1", "name": "Song A", "artists": ["Artist"]}],
        )

    def test_none_return_is_empty_list(self):
        self.assertEqual(search_tracks_service(self._player(None), "x"), [])

    def test_missing_tracks_key_is_empty_list(self):
        self.assertEqual(
            search_tracks_service(self._player({"albums": [{"id": "a"}]}), "x"),
            [],
        )

    def test_skips_non_dict_entries(self):
        raw = {"tracks": [{"id": "1"}, "stray-string", None]}
        result = search_tracks_service(self._player(raw), "x")
        self.assertEqual(result, [{"id": "1", "name": None, "artists": []}])
