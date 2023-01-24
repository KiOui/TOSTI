from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from thaliedje.models import (
    SpotifyQueueItem,
)


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
