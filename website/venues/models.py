from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from associations.models import Association

User = get_user_model()


class Venue(models.Model):
    """Venue model class."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=100, auto_created=True)
    active = models.BooleanField(default=True)
    color_in_calendar = models.CharField(
        max_length=50, help_text="Color of reservations shown in calendar.", null=True, blank=True
    )
    can_be_reserved = models.BooleanField(default=True)

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

    title = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations")
    association = models.ForeignKey(
        Association, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reservations")
    comment = models.TextField(null=True, blank=True)

    def clean(self):
        """Clean model."""
        super(Reservation, self).clean()
        if self.end_time is not None and self.start_time is not None and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End date cannot be before start date."})

    def __str__(self):
        """Convert this object to string."""
        return "{} ({} - {})".format(self.venue, self.start_time, self.end_time)
