from constance import config
from django_cron import CronJobBase, Schedule

from thaliedje import services
from thaliedje.models import Player


class StopMusicCronJob(CronJobBase):
    RUN_AT_TIMES = [config.THALIEDJE_STOP_MUSIC_TIME]
    RETRY_AFTER_FAILURE_MINS = 5
    schedule = Schedule(run_at_times=RUN_AT_TIMES, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "thaliedje.stopmusic"

    def do(self):
        for player in Player.objects.all():
            services.player_pause(player)


class StartMusicCronJob(CronJobBase):
    RUN_AT_TIMES = [config.THALIEDJE_START_MUSIC_TIME]
    RETRY_AFTER_FAILURE_MINS = 5
    schedule = Schedule(run_at_times=RUN_AT_TIMES, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = "thaliedje.startmusic"

    def do(self):
        for player in Player.objects.all():
            services.player_start(player)
