from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone

from thaliedje.models import (
    SpotifyPlayer,
    SpotifyQueueItem,
    SpotifyTrack,
)
from tosti.metrics import emit as emit_metric

User = get_user_model()


def request_song(player, user, track_id):
    """Request a song."""
    if not player.can_request_song(user):
        raise PermissionDenied("User is not allowed to request songs.")

    track_info = player.request_song(track_id)

    queued_track = SpotifyQueueItem.queue_track(track_info, player, user)
    emit_metric("song_requested", venue=str(player))
    return queued_track


def observe_player_state(player) -> dict:
    """Reconcile the live Spotify queue with our ``SpotifyQueueItem`` log.

    Walks the Spotify-side queue + currently-playing track and updates two
    fields on TOSTI's request log:

    * ``observed_at_position`` — pinned to the position we last saw the
      request at (0 = next-to-play, 1 = after that, …). Once set this is the
      stable join key the enricher uses to attribute Spotify queue entries
      to TOSTI requests, avoiding the ambiguity of pure FIFO matching when
      the same track is queued multiple times.

    * ``played_at`` — set to ``timezone.now()`` when a previously-seen
      request is no longer in ``queue`` and is no longer ``currently_playing``.
      It's possible the operator skipped it rather than letting it play —
      we can't distinguish from outside, and the user doesn't care.

    Matching strategy: walk the Spotify queue top-down (= play order) and
    for each entry claim the oldest unmatched-or-currently-positioned TOSTI
    row with the same ``track_id``. Items added by the operator from
    outside TOSTI have no DB row and stay unattributed. Items in our DB
    that the operator queued the same track for (and our row's slot was
    "stolen") will appear unattributed in the merged view; that's the
    honest outcome given we can't tell whose add hit which slot.

    Returns a small counters dict for metrics/logging — does not raise on
    transient Spotify failures (``player.queue`` already returns None on
    error; we just leave the state alone until the next run).
    """
    if not isinstance(player, SpotifyPlayer):
        return {"skipped": "not_a_spotify_player"}

    spotify_queue = player.queue
    if spotify_queue is None:
        return {"skipped": "queue_unavailable"}

    # currently_playing is a separate Spotify endpoint; we already cache it.
    playback = player._current_playback
    currently_playing_id = None
    if playback and isinstance(playback, dict):
        item = playback.get("item")
        if isinstance(item, dict):
            currently_playing_id = item.get("id")

    # All TOSTI rows we haven't yet marked as played, for this player. We
    # restrict to "today" only as a guardrail against the observer
    # accidentally claiming an ancient unfinished row after a long outage;
    # in practice anything still unplayed from yesterday is noise.
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    open_rows = list(
        SpotifyQueueItem.objects.select_related("track")
        .filter(player=player, added__gte=today, played_at__isnull=True)
        .order_by("added")
    )

    # Group open rows by track_id for cheap O(1) claim-from-front.
    by_track: dict[str, list[SpotifyQueueItem]] = {}
    for row in open_rows:
        if row.track is None:
            continue
        by_track.setdefault(row.track.track_id, []).append(row)

    claimed: set[int] = set()
    positions_changed = 0

    for position, entry in enumerate(spotify_queue):
        track_id = entry.get("track_id")
        if not track_id:
            continue
        bucket = by_track.get(track_id)
        if not bucket:
            continue
        # Prefer a row that was already pinned to a position close to this
        # one (smooth transitions as the queue advances); otherwise take
        # the oldest unclaimed.
        chosen = bucket.pop(0)
        if chosen.observed_at_position != position:
            chosen.observed_at_position = position
            chosen.save(update_fields=["observed_at_position"])
            positions_changed += 1
        claimed.add(chosen.id)

    # Anything previously observed but no longer in queue or currently
    # playing is considered "played" (or skipped — same end state from
    # outside).
    now = timezone.now()
    played_count = 0
    for row in open_rows:
        if row.id in claimed:
            continue
        if row.observed_at_position is None:
            # Never seen on Spotify in the first place. Could be
            # consumed-between-polls or stolen by an out-of-band operator
            # add. Mark as played to keep the working set bounded — the
            # honest unknown.
            row.played_at = now
            row.save(update_fields=["played_at"])
            played_count += 1
            continue
        # We did see it before, but not this round. If it's the currently
        # playing track, leave played_at alone — we'll mark it once it
        # advances. Otherwise it's gone.
        if row.track and row.track.track_id == currently_playing_id:
            continue
        row.played_at = now
        row.save(update_fields=["played_at"])
        played_count += 1

    return {
        "queue_length": len(spotify_queue),
        "open_rows": len(open_rows),
        "claimed": len(claimed),
        "positions_changed": positions_changed,
        "newly_played": played_count,
    }


def enrich_spotify_queue(player) -> list[dict] | None:
    """Return Spotify's live queue annotated with TOSTI request metadata.

    For each Spotify queue entry adds (when known):

    * ``requested_by`` — the TOSTI display name + username of the user who
      requested it, or ``None`` if the track was queued from outside TOSTI
      or the observer hasn't matched it yet.
    * ``requested_at`` — ISO timestamp of the original TOSTI request.

    Returns ``None`` if Spotify's queue is unavailable (matching the
    existing ``Player.queue`` contract). The merged view is read-only and
    safe to call on every UI poll; the underlying ``player.queue`` is
    already cached for 5s.
    """
    if not isinstance(player, SpotifyPlayer):
        return player.queue

    raw = player.queue
    if raw is None:
        return None

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    open_rows = list(
        SpotifyQueueItem.objects.select_related("track", "requested_by")
        .filter(player=player, added__gte=today, played_at__isnull=True)
        .order_by("added")
    )

    # Two indices to support the join: by (track_id, position) for the
    # stable case where the observer pinned a position, and by track_id
    # for the fallback "we have a row but no position yet" case.
    by_pos: dict[tuple[str, int], SpotifyQueueItem] = {}
    by_track_fallback: dict[str, list[SpotifyQueueItem]] = {}
    for row in open_rows:
        if row.track is None:
            continue
        if row.observed_at_position is not None:
            by_pos[(row.track.track_id, row.observed_at_position)] = row
        else:
            by_track_fallback.setdefault(row.track.track_id, []).append(row)

    enriched: list[dict] = []
    for position, entry in enumerate(raw):
        track_id = entry.get("track_id")
        row: SpotifyQueueItem | None = by_pos.get((track_id, position))
        if row is None:
            bucket = by_track_fallback.get(track_id)
            if bucket:
                row = bucket.pop(0)
        enriched.append(
            {
                **entry,
                "requested_by": _serialise_requester(row.requested_by) if row else None,
                "requested_at": row.added.isoformat() if row else None,
            }
        )
    return enriched


def _serialise_requester(user) -> dict | None:
    """Return a compact JSON-friendly user representation for the merged queue.

    Mirrors the safer subset of fields ``users.api.v1.serializers.UserSerializer``
    exposes — enough to render "requested by Alice" without dumping the full
    user object into the public queue endpoint.
    """
    if user is None:
        return None
    return {
        "id": user.pk,
        "display_name": str(user),
        "username": user.username,
    }


def execute_data_minimisation(dry_run=False):
    """
    Remove song-request history from users that is more than 31 days old.

    :param dry_run: does not really remove data if True
    :return: list of users from who data is removed
    """
    delete_before = timezone.now() - timedelta(days=31)
    requests = SpotifyQueueItem.objects.filter(added__lte=delete_before)

    users = []
    for request in requests:
        users.append(request.requested_by)
        request.requested_by = None
        if not dry_run:
            request.save()
    return users


def generate_most_requested_songs():
    """Generate statistics about the most requested songs."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for song in SpotifyTrack.objects.annotate(
        requested_amount=Count("requests", filter=Q(requests__added__gte=last_year))
    ).order_by("-requested_amount")[:10]:
        data["labels"].append(str(song.track_name))
        data["datasets"][0]["data"].append(song.requested_amount)

    return data


def generate_users_with_most_song_requests():
    """Generate statistics about users with the most song requests."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for user in User.objects.annotate(
        requested_amount=Count("requests", filter=Q(requests__added__gte=last_year))
    ).order_by("-requested_amount")[:10]:
        data["labels"].append(str(user))
        data["datasets"][0]["data"].append(user.requested_amount)

    return data
