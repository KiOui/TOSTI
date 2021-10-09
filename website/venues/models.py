from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Venue(models.Model):
    """Venue model class."""

    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)
    color_in_calendar = models.CharField(
        max_length=50, help_text="Color of reservations shown in calendar.", null=True
    )

    class Meta:
        """Meta class."""

        ordering = ["-active", "name"]

    def __str__(self):
        """
        Convert this object to string.

        :return: the name of this Venue
        """
        return self.name


class Reservation(models.Model):
    """Reservation model class."""

    name = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reservations")

    def save(self, *args, **kwargs):
        """Save model."""
        if self.end_time <= self.start_time:
            raise ValueError("End date cannot be before start date.")

        super(Reservation, self).save(*args, **kwargs)

    def __str__(self):
        """Convert this object to string."""
        return "{} ({} - {})".format(self.venue, self.start_time, self.end_time)
