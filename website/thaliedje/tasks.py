from celery import shared_task
from constance import config

from thaliedje.models import SpotifyPlayer
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
