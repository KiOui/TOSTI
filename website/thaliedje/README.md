# `thaliedje/` &mdash; canteen music players

Thaliedje runs the shared jukebox in the Huygens canteens. Anyone with a Radboud account can request a song; the player plays it in the canteen for everyone there to hear.

There are two backends: **Spotify** (Noordkantine) and **Marietje** (Zuidkantine, read-only). They share a base `Player` model and a polymorphism layer (`InheritanceManager`), so most code paths can treat them uniformly.

## Data model

```mermaid
classDiagram
    direction LR
    Player <|-- SpotifyPlayer
    Player <|-- MarietjePlayer
    Player --> Venue : one per venue
    SpotifyQueueItem --> Player
    SpotifyQueueItem --> SpotifyTrack
    SpotifyQueueItem --> User : requested by
    SpotifyTrack --> "0..*" SpotifyArtist
    ThaliedjeBlacklistedUser --> User
    ThaliedjeControlEvent --> Venue : event-time perms
    PlayerLogEntry --> Player
    PlayerLogEntry --> User
```

- **`Player`** is the abstract base (slug, venue). Concrete subclasses `SpotifyPlayer` and `MarietjePlayer` implement `request_song`, `queue`, `current_track_name`, etc.
- **`SpotifyPlayer`** holds the OAuth credentials for the Spotify account that powers a venue. It's also where playback state (current track, queue, shuffle, repeat) is read from.
- **`MarietjePlayer`** wraps the (read-only) Marietje API for Zuidkantine. It can report what's playing but not queue, search, or control.
- **`SpotifyQueueItem`** is the TOSTI-side request log: which user requested which track at which time on which player.
- **`SpotifyTrack` / `SpotifyArtist`** are denormalised caches so the request log keeps making sense after a track is removed from Spotify.
- **`ThaliedjeBlacklistedUser`** &mdash; same idea as `OrderBlacklistedUser` but for song-request abuse.
- **`ThaliedjeControlEvent`** lets a reservation event override the default request/control permissions for the duration of the booking (e.g. a private borrel where only the organisers can queue).
- **`PlayerLogEntry`** is the audit log for control-plane actions (start, pause, next, etc.).

## Always use `select_subclasses()`

`Player.objects.get(...)` returns a base-class instance with all the `current_*` properties raising `NotImplementedError`. Always go through the `InheritanceManager`:

```python
player = Player.objects.select_subclasses().get(venue__slug=slug)
```

There's a helper in `mcp.py:get_player_for_venue` that does this. Use it.

## The auto-start trap

`SpotifyPlayer.request_song` queues the track. If the player is paused, it used to also try to start playback + skip to the new track. That can silently consume the just-queued song when Spotify rejects the `start_playback` call (which happens any time there's no active context &mdash; typical off-hours state). The current implementation only auto-starts when `_current_playback is not None`. See the regression tests in `tests/test_player.py`.

If you need to touch `request_song` again, re-read those tests first.

## Spotify API quirks worth knowing

- **`do_spotify_request` swallows `SpotifyException` and `ReadTimeout`.** Failed calls return `None`. Useful for resilience but easy to miss when debugging &mdash; if a behaviour you expected didn't happen, check Sentry logs for a "Spotify error" line.
- **`spotify.queue()` lags.** A track that just started playing can still appear at queue position 0 for a few seconds. The merged-queue work (see `services.py:observe_player_state` if present) tolerates this; new code should too.
- **`spotify.search()` returns a dict keyed by query type**, not a flat list of tracks. The MCP `search_tracks` service normalises both into the same flat shape; if you call `player.search()` directly, expect `{"tracks": [...], "albums": [...]}`.

## MCP

This app exposes `get_player_state`, `search_tracks`, and `request_song` to AI assistants. `search_tracks` is `openWorldHint: True` (it queries Spotify's external catalogue); `request_song` requires the `thaliedje:request` scope. See `mcp.py`.

## Tests

- `tests/test_mcp.py` covers the MCP tools and the `search_tracks` shape normalisation (regression for the Sentry crash from iterating Spotify's dict as a list).
- `tests/test_player.py` covers the `request_song` auto-start logic and Spotify projection.
</content>
</invoke>