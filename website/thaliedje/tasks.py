from celery import shared_task
from constance import config

from thaliedje.models import SpotifyPlayer


@shared_task
def thaliedje_stop_music():
    """Stop the music."""
    for player in SpotifyPlayer.objects.all():
        try:
            player.pause()
        except Exception:
            # Ignore errors when stopping the music
            pass


@shared_task
def thaliedje_start_music():
    """Start the music."""
    if config.THALIEDJE_HOLIDAY_ACTIVE:
        return

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
        except Exception:
            # Ignore errors when starting the music
            pass
