"""Tests for the Spotify/Marietje player models."""

from unittest.mock import MagicMock, PropertyMock, patch

from django.test import TestCase

from thaliedje.models import SpotifyPlayer


class SpotifyPlayerRequestSongTests(TestCase):
    """Regression tests for ``SpotifyPlayer.request_song``.

    Background: when a song is queued via ``add_to_queue`` and the player
    happens to be paused, the old implementation always called ``start()``
    + ``next()`` to bring the user's track to the front. On a player with
    no active context (typical off-hours state) ``start_playback`` 403s
    silently ("Restriction violated"), and the subsequent ``next_track``
    then *consumes* the just-queued track from Spotify's queue — leaving
    the user with a ``SpotifyQueueItem`` row in TOSTI's DB but nothing on
    Spotify. We now skip the auto-start when ``_current_playback`` is
    None.
    """

    def _player(self):
        # Use ``new`` so the model isn't saved (and we don't need a venue
        # or unique-field setup); we only care about method behaviour.
        return SpotifyPlayer(
            client_id="ci",
            client_secret="cs",
            redirect_uri="https://example.com/cb",
            playback_device_id="dev-1",
        )

    def _run_request_song(self, is_playing, current_playback):
        """Drive ``request_song`` with a mocked Spotify client.

        Returns the list of Spotify-API function references the player
        attempted to call, so individual tests can assert against the set.
        """
        player = self._player()
        # ``do_spotify_request`` is called from request_song for track(),
        # add_to_queue(), and from start()/next(); patch it to a no-op.
        player.do_spotify_request = MagicMock(return_value={"id": "track"})
        spotify_stub = MagicMock()
        with (
            patch.object(
                SpotifyPlayer,
                "spotify",
                new_callable=PropertyMock,
                return_value=spotify_stub,
            ),
            patch.object(
                SpotifyPlayer,
                "is_playing",
                new_callable=PropertyMock,
                return_value=is_playing,
            ),
            patch.object(
                SpotifyPlayer,
                "_current_playback",
                new_callable=PropertyMock,
                return_value=current_playback,
            ),
        ):
            player.request_song("track-id-1")
        return spotify_stub, [
            call.args[0] for call in player.do_spotify_request.call_args_list
        ]

    def test_does_not_auto_start_when_no_active_context(self):
        """Player paused AND no active context → only queue, no start/next."""
        spotify, called_funcs = self._run_request_song(
            is_playing=False, current_playback=None
        )
        # add_to_queue + track were called; start_playback / next_track
        # must NOT have been — that's what eats the queued track.
        self.assertIn(spotify.track, called_funcs)
        self.assertIn(spotify.add_to_queue, called_funcs)
        self.assertNotIn(spotify.start_playback, called_funcs)
        self.assertNotIn(spotify.next_track, called_funcs)

    def test_does_auto_start_when_paused_but_has_active_context(self):
        """Player paused but a context IS loaded → still auto-start/skip."""
        spotify, called_funcs = self._run_request_song(
            is_playing=False, current_playback={"some": "ctx"}
        )
        self.assertIn(spotify.start_playback, called_funcs)
        self.assertIn(spotify.next_track, called_funcs)

    def test_does_not_auto_start_when_already_playing(self):
        """Player already playing → no auto-start (Spotify will play the queue itself)."""
        spotify, called_funcs = self._run_request_song(
            is_playing=True, current_playback={"some": "ctx"}
        )
        self.assertNotIn(spotify.start_playback, called_funcs)
        self.assertNotIn(spotify.next_track, called_funcs)
