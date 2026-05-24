"""Tests for the thaliedje app's MCP toolset."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from thaliedje.mcp import ThaliedjeTools
from thaliedje.models import MarietjePlayer
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
        with patch("thaliedje.mcp.request_song_service") as mock_service:
            queued = MagicMock()
            queued.track.track_name = "Test Track"
            mock_service.return_value = queued

            result = tools.request_song(venue_slug=venue.slug, track_id="track-id-42")

        mock_service.assert_called_once()
        args, _ = mock_service.call_args
        # Player.objects.get may return the base ``Player`` type even though
        # we created a MarietjePlayer; compare by primary key.
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
