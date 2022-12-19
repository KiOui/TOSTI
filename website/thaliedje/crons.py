from constance import config
from django_cron import CronJobBase, Schedule

from thaliedje.models import Player


class StopMusicCronJob(CronJobBase):
    """Stop the music at a specific time every day."""

    RUN_AT_TIMES = [config.THALIEDJE_STOP_PLAYERS_AT]
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_at_times=RUN_AT_TIMES, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "thaliedje.stopmusic"

    def do(self):
        """Stop the music."""
        for player in Player.objects.all():
            player.spotify.pause_playback()


class StartMusicCronJob(CronJobBase):
    """Start the music at a specific time every day."""

    RUN_AT_TIMES = [config.THALIEDJE_START_PLAYERS_AT]
    RETRY_AFTER_FAILURE_MINS = 1
    schedule = Schedule(run_at_times=RUN_AT_TIMES, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "thaliedje.startmusic"

    def do(self):
        """Start the music."""
        for player in Player.objects.all():
            player.spotify.start_playback()
