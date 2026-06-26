"""MCP tools exposed by the thaliedje app."""

from django.core.exceptions import PermissionDenied

from mcp_server import MCPToolset

from thaliedje.services import (
    get_player_for_venue,
    get_player_state,
    request_song,
    search_tracks,
)
from tosti.mcp import require_scope


class ThaliedjeTools(MCPToolset):
    """Music-player tools (read state, search, queue requests).

    These methods are thin wrappers around ``thaliedje.services``; business
    logic lives there so the API views and the MCP tools share one
    implementation.
    """

    def get_player_state(self, venue_slug: str) -> dict:
        """Return what the music player at the given venue is doing right now.

        ``venue_slug`` matches the slug returned by ``list_venues``. The result
        includes the current track (if any), play state, shuffle, and repeat.
        """
        player = get_player_for_venue(venue_slug)
        if player is None:
            return {"error": f"No player configured for venue '{venue_slug}'."}
        return get_player_state(player)

    def search_tracks(self, venue_slug: str, query: str, maximum: int = 5) -> dict:
        """Search the music catalog for tracks via a venue's player.

        ``venue_slug`` selects the player (each venue has its own backend —
        Spotify or Marietje). ``query`` is a free-text search. ``maximum``
        caps the number of results (default 5, hard ceiling 25).
        """
        player = get_player_for_venue(venue_slug)
        if player is None:
            return {"error": f"No player configured for venue '{venue_slug}'."}

        if not player.can_request_song(self.request.user):
            return {"error": "You are not allowed to request songs on this player."}

        return {
            "query": query,
            "venue": str(player.venue),
            "results": search_tracks(player, query, maximum=maximum),
        }

    def request_song(self, venue_slug: str, track_id: str) -> dict:
        """Request a song to be added to a venue's player queue.

        ``track_id`` is the ``id`` returned by ``search_tracks``.
        Requires the ``thaliedje:request`` OAuth2 scope.
        """
        scope_error = require_scope(self.request, "thaliedje:request")
        if scope_error:
            return {"error": scope_error}

        player = get_player_for_venue(venue_slug)
        if player is None:
            return {"error": f"No player configured for venue '{venue_slug}'."}

        try:
            queued = request_song(player, self.request.user, track_id)
        except PermissionDenied as e:
            return {"error": str(e)}
        except Exception as e:  # external player API failures, etc.
            return {"error": f"Could not queue track: {e}"}

        return {
            "queued": True,
            "venue": str(player.venue),
            "track": {
                "id": track_id,
                "name": getattr(getattr(queued, "track", None), "track_name", None),
            },
        }
