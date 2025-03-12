from django.db import models


class CronJobLog(models.Model):
    """Keep track of the cron jobs that ran and any error messages."""

    code = models.CharField(max_length=64, db_index=True)
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    is_success = models.BooleanField(default=False)
    message = models.TextField(default="", blank=True)

    # This field is used to mark jobs executed in exact time.
    # Jobs that run every X minutes, have this field empty.
    ran_at_time = models.TimeField(null=True, blank=True, db_index=True, editable=False)

    def __unicode__(self):
        """Return a Unicode representation of the cron_job."""
        return "{} ({})".format(self.code, "Success" if self.is_success else "Fail")

    def __str__(self):
        """Return a string representation of the cron_job."""
        return "{} ({})".format(self.code, "Success" if self.is_success else "Fail")

    class Meta:
        """Meta class."""

        indexes = [
            models.Index(fields=["code", "is_success", "ran_at_time"]),
            models.Index(fields=["code", "start_time", "ran_at_time"]),
            models.Index(
                fields=[
                    "code",
                    "start_time",
                ]
            ),  # useful when finding latest run (order by start_time) of cron
        ]
        app_label = "cron"


class CronJobLock(models.Model):
    """Lock on a cron job."""

    job_name = models.CharField(max_length=200, unique=True)
    locked = models.BooleanField(default=False)
