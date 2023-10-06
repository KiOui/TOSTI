from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone

from thaliedje.models import (
    SpotifyQueueItem,
    SpotifyTrack,
)


User = get_user_model()


def request_song(player, user, track_id):
    """Request a song."""
    if not player.can_request_song(user):
        raise PermissionDenied("User is not allowed to request songs.")

    track_info = player.request_song(track_id)

    queued_track = SpotifyQueueItem.queue_track(track_info, player, user)
    return queued_track


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
