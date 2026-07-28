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
    The shape mirrors what the REST API returns so the MCP surface is a
    strict subset of the REST surface (no MCP-only data leaks). Per-track
    fields: ``id`` (Spotify track ID), ``name``, ``artists``, ``album``,
    ``album_release_date``, ``duration_ms``, ``image`` (album cover URL,
    or None).
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
            "album": r.get("album"),
            "album_release_date": r.get("album_release_date"),
            "duration_ms": r.get("duration_ms"),
            "image": r.get("image"),
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
        """Search the Spotify catalog for tracks playable on a venue's player.

        The catalog is **Spotify's** — results are real Spotify tracks and
        the ``id`` field on each result is a **Spotify track ID** (an
        opaque base62 string, e.g. ``"7D5vAulNfrQV6xEwzgH0OF"``). Pass it
        through verbatim to ``request_song``; do not parse, hash, or
        invent it.

        ``venue_slug`` selects the player. Search currently works only
        for Spotify-backed venues; Marietje-backed venues return an
        empty list (Marietje does not expose a catalog search). The
        agent should not interpret an empty result on a Marietje venue
        as "no songs match" — say so explicitly to the user.
        ``query`` is a free-text search — Spotify will accept
        ``track:name artist:artistname`` for more precise matching if you
        already know both. ``maximum`` caps the number of results
        (default 5, hard ceiling 25).

        **Result order is Spotify's relevance/popularity ranking** — the
        first entry is the best match Spotify could find, the last is the
        weakest. A few important consequences:

        - Lower-position entries may not be exact name matches; Spotify
          sometimes surfaces other songs by the same artist. Trust
          ``name`` + ``artists`` for relevance, not just position.
        - The same song often exists under multiple Spotify IDs (album
          version, single, live recording, remaster, regional release).
          Use ``album``, ``album_release_date`` and ``duration_ms`` to
          tell them apart when ``name`` and ``artists`` match. If the
          user said "the original" prefer the earliest
          ``album_release_date``; if they said "the album version"
          prefer the entry whose ``album`` is the studio album rather
          than a compilation or single.
        - ``image`` is the album cover URL — surface it to the user if
          your client renders inline images so they can confirm by sight.
          You can also point the user at
          ``https://open.spotify.com/track/{id}`` for a visual confirm.
        - When in doubt with multiple plausible matches, ask the user
          rather than guessing — every result here is genuinely a
          distinct Spotify recording.

        Per-track fields: ``id`` (Spotify track ID), ``name``,
        ``artists`` (list of names), ``album`` (album name),
        ``album_release_date``, ``duration_ms``, ``image`` (album cover
        URL or ``null``).
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

        ``track_id`` is a **Spotify track ID** (the opaque ``id`` field
        returned by ``search_tracks``) — pass it through verbatim.
        Do not pass a URI (``spotify:track:...``), URL, ISRC, or made-up
        identifier; only the bare ID Spotify returned in the search.
        Requires the ``thaliedje:request`` OAuth2 scope.

        Confirm with the user which specific result they want before
        calling this — two search hits with the same ``name`` and
        ``artists`` can be entirely different recordings.
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
