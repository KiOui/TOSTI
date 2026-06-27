"""MCP tools exposed by the thaliedje app."""

from django.core.exceptions import PermissionDenied

from mcp_server import MCPToolset

from thaliedje.services import (
    request_song,
)
from thaliedje.models import Player
from tosti.mcp import require_scope


def get_player_for_venue(venue_slug: str) -> Player | None:
    """Return the concrete ``Player`` configured for the given venue, or ``None``.

    Uses ``InheritanceManager.select_subclasses()`` so we get a fully-loaded
    ``SpotifyPlayer`` or ``MarietjePlayer`` — the base ``Player.current_*``
    properties raise ``NotImplementedError`` and the subclass-specific state
    (auth, URL) only loads on the subclass.
    """
    try:
        return Player.objects.select_subclasses().get(venue__slug=venue_slug)
    except Player.DoesNotExist:
        return None


def search_tracks(player: Player, query: str, maximum: int = 5) -> list[dict]:
    """Search the player's catalog for tracks. Caller is responsible for permission checks.

    ``Player.search`` returns different shapes depending on the backend:
    - ``SpotifyPlayer`` returns a dict keyed by query type, e.g.
      ``{"tracks": [{...}, ...]}``.
    - ``MarietjePlayer`` returns ``None`` (no search support).

    Normalise both to the flat list of track dicts the MCP tool promises.
    """
    maximum = max(1, min(int(maximum), 25))
    raw = player.search(query, maximum=maximum, query_type="track")
    if not raw:
        return []
    # SpotifyPlayer wraps results in {"tracks": [...]}; pull the list out.
    # Any other shape (e.g. a future backend that returns a flat list)
    # is passed through unchanged.
    if isinstance(raw, dict):
        tracks = raw.get("tracks", [])
    else:
        tracks = raw
    return [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "artists": r.get("artists", []),
        }
        for r in tracks
        if isinstance(r, dict)
    ]


class ThaliedjeTools(MCPToolset):
    """Music-player tools (read state, search, queue requests).

    These methods are thin wrappers around ``thaliedje.services``; business
    logic lives there so the API views and the MCP tools share one
    implementation.
    """

    # See ``tosti.mcp.stamp_tool_annotations`` for what these do. ``search_tracks``
    # is openWorld because it queries an external catalog (Spotify / Marietje).
    tool_annotations = {
        "get_player_state": {
            "readOnlyHint": True,
            "openWorldHint": False,
            "title": "Get player state",
        },
        "search_tracks": {
            "readOnlyHint": True,
            "openWorldHint": True,
            "title": "Search the music catalog",
        },
        "request_song": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
            "title": "Request a song",
        },
    }

    def get_player_state(self, venue_slug: str) -> dict:
        """Return what the music player at the given venue is doing right now.

        ``venue_slug`` matches the slug returned by ``list_venues``. The result
        includes the current track (if any), play state, shuffle, and repeat.
        """
        player = get_player_for_venue(venue_slug)
        if player is None:
            return {"error": f"No player configured for venue '{venue_slug}'."}

        return {
            "venue": str(player.venue),
            "is_playing": bool(getattr(player, "is_playing", False)),
            "shuffle": getattr(player, "shuffle", None),
            "repeat": getattr(player, "repeat", None),
            "track": {
                "name": player.current_track_name,
                "artists": player.current_artists,
                "image": player.current_image,
            },
        }

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
