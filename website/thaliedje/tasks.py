from celery import shared_task
from constance import config

from thaliedje.models import SpotifyPlayer
from thaliedje.services import observe_player_state
from tosti.metrics import emit as emit_metric


@shared_task
def thaliedje_stop_music():
    """Stop the music."""
    stopped = 0
    failed = 0
    for player in SpotifyPlayer.objects.all():
        try:
            player.pause()
            stopped += 1
        except Exception:
            # Ignore errors when stopping the music
            failed += 1
    emit_metric("cron_stop_music_run", stopped=stopped, failed=failed)


@shared_task
def thaliedje_start_music():
    """Start the music."""
    if config.THALIEDJE_HOLIDAY_ACTIVE:
        emit_metric("cron_start_music_run", skipped_reason="holiday")
        return

    started = 0
    failed = 0
    for player in SpotifyPlayer.objects.all():
        try:
            player.repeat = "context"
            player.shuffle = True

            if (
                config.THALIEDJE_START_PLAYER_URI is not None
                and config.THALIEDJE_START_PLAYER_URI != ""
            ):
                player.start_playing(config.THALIEDJE_START_PLAYER_URI)
            else:
                player.start()
            started += 1
        except Exception:
            # Ignore errors when starting the music
            failed += 1
    emit_metric("cron_start_music_run", started=started, failed=failed)


@shared_task
def thaliedje_observe_queue_state():
    """Poll every Spotify player and update its request log.

    Drives the ``observed_at_position`` / ``played_at`` state machine on
    ``SpotifyQueueItem`` so the merged-queue read path has a stable join
    key (track_id + position) rather than guessing FIFO. Register via
    django_celery_beat to run every ~30s during venue hours; the function
    is idempotent and safe to call concurrently with itself.

    Failures (Spotify rate-limit, transient HTTP error) are swallowed
    per-player so one bad player doesn't poison the rest. The cost of a
    missed poll is a slightly stale merged view, not a broken one.
    """
    polled = 0
    failed = 0
    for player in SpotifyPlayer.objects.all():
        try:
            observe_player_state(player)
            polled += 1
        except Exception:
            failed += 1
    emit_metric("cron_observe_queue_state_run", polled=polled, failed=failed)
