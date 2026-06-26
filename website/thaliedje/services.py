from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone

from thaliedje.models import (
    Player,
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


def get_player_state(player: Player) -> dict:
    """Snapshot a player's current playback state as a JSON-friendly dict."""
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


def search_tracks(player: Player, query: str, maximum: int = 5) -> list[dict]:
    """Search the player's catalog for tracks. Caller is responsible for permission checks."""
    maximum = max(1, min(int(maximum), 25))
    raw = player.search(query, maximum=maximum, query_type="track") or []
    return [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "artists": r.get("artists", []),
        }
        for r in raw
    ]


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
