from constance import config
from cron.core import CronJobBase, Schedule

from thaliedje.models import SpotifyPlayer


WEEKDAYS = [0, 1, 2, 3, 4]
WEEKENDS = [5, 6]


class StopMusicCronJob(CronJobBase):
    """Stop the music at a specific time every day."""

    RUN_AT_TIMES = [config.THALIEDJE_STOP_PLAYERS_AT]
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(
        run_at_times=RUN_AT_TIMES, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS
    )
    code = "thaliedje.stopmusic"

    def do(self):
        """Stop the music."""
        for player in SpotifyPlayer.objects.all():
            try:
                player.pause()
            except Exception:
                # Ignore errors when stopping the music
                pass


class StartMusicCronJob(CronJobBase):
    """Start the music at a specific time every day."""

    RUN_AT_TIMES = [config.THALIEDJE_START_PLAYERS_AT]
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(
        run_at_times=RUN_AT_TIMES,
        retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS,
        run_weekly_on_days=WEEKDAYS,
    )
    code = "thaliedje.startmusic"

    def do(self):
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
