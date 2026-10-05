"""Tests for player log retention."""

from django.test import TestCase

from thaliedje.models import PlayerLogEntry, SpotifyPlayer


class PlayerLogEntryTests(TestCase):
    def test_log_keeps_player_name_after_spotify_player_is_deleted(self):
        player = SpotifyPlayer.objects.create(
            display_name="Canteen Spotify",
            slug="canteen-spotify",
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="https://example.com/callback",
        )
        player.log_action(None, "play", "Started playback.")
        log = PlayerLogEntry.objects.get(player=player)

        player.delete()

        log.refresh_from_db()
        self.assertIsNone(log.player)
        self.assertEqual(log.player_name, "Canteen Spotify")
        self.assertIn("Canteen Spotify", str(log))
