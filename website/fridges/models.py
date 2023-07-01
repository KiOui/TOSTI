from datetime import timedelta

from django.db import models
from django.utils import timezone
from oauth2_provider.models import Application


class Fridge(models.Model):
    """A fridge."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    venue = models.ForeignKey("venues.Venue", on_delete=models.PROTECT, null=True, blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="If the fridge is active, it will be shown on the website and can be opened by users within the set "
        "opening hours. People with 'open always' permissions can always open the fridge, regardless of "
        "whether it is active.",
    )
    unlock_for_how_long = models.DurationField(
        default=timedelta(minutes=1), help_text="How long to unlock the fridge for by default (HH:MM:SS)."
    )

    oauth_client = models.ForeignKey(
        Application,
        on_delete=models.PROTECT,
        help_text="The OAuth2 client that may request opening the fridge.",
        related_name="fridges",
    )

    def __str__(self):
        return self.name

    @property
    def last_opened(self):
        """Return the last time the fridge was opened."""
        try:
            return self.accesslog_set.latest().timestamp
        except AccessLog.DoesNotExist:
            return None

    @property
    def last_opened_by(self):
        """Return the last user to open the fridge."""
        try:
            return self.accesslog_set.latest().user
        except AccessLog.DoesNotExist:
            return None

    @property
    def current_opening_hours(self):
        current_time = timezone.now().astimezone()
        weekday = current_time.weekday()
        opening_hours = self.generalopeninghours_set.filter(
            weekday=weekday, start_time__lte=current_time.time(), end_time__gte=current_time.time()
        )
        return opening_hours

    @property
    def can_be_opened(self):
        return self.current_opening_hours.filter(
            restrict_to_groups__isnull=True,
        ).exists()

    def opens_today_at(self):
        """Return the time the fridge opens today, or None if it doesn't open today."""
        current_time = timezone.now().astimezone()

        if self.can_be_opened:
            return current_time.time()

        next_opening_times_today = (
            self.generalopeninghours_set.filter(
                weekday=current_time.weekday(),
                start_time__gte=current_time.time(),
                restrict_to_groups__isnull=True,
            )
            .order_by("start_time")
            .first()
        )

        if next_opening_times_today:
            return next_opening_times_today.start_time
        return None

    class Meta:
        verbose_name = "fridge"
        verbose_name_plural = "fridges"
        ordering = ["name"]
        permissions = [
            ("open_always", "Can always open fridges"),
        ]


class GeneralOpeningHours(models.Model):
    """General opening hours for a fridge."""

    DAY_CHOICES = (
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    )

    weekday = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    fridge = models.ForeignKey(Fridge, on_delete=models.CASCADE)

    restrict_to_groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        help_text="Only allow members of these groups to open the fridge during these opening hours.",
    )

    def __str__(self):
        return f"{self.DAY_CHOICES[self.weekday][1]} {self.start_time} - {self.end_time}"

    class Meta:
        verbose_name = "general opening hours"
        verbose_name_plural = "general opening hours"
        ordering = ["weekday", "start_time"]
        unique_together = ["weekday", "start_time", "end_time", "fridge"]


class BlacklistEntry(models.Model):
    """A blacklist entry."""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    fridge = models.ForeignKey(Fridge, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} blacklisted from {self.fridge}"

    class Meta:
        verbose_name = "blacklist entry"
        verbose_name_plural = "blacklist entries"


class AccessLog(models.Model):
    """A log of when a user accessed a fridge."""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    fridge = models.ForeignKey(Fridge, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} accessed {self.fridge} at {self.timestamp:%Y-%m-%d %H:%M}"

    class Meta:
        verbose_name = "access log"
        verbose_name_plural = "access logs"
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"
