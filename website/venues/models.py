from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from associations.models import Association

User = get_user_model()


class VenueQuerySet(models.QuerySet):
    """Venue queryset."""

    def active(self):
        """Filter for active venues."""
        return self.filter(active=True)


class VenueManager(models.Manager):
    """Custom venue manager."""

    def get_queryset(self):
        """Use the VenueQuerySet."""
        return VenueQuerySet(self.model, using=self._db)

    def active_venues(self):
        """Return active venues only."""
        return self.get_queryset().active()


class Venue(models.Model):
    """Venue model class."""

    objects = VenueManager()
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=100)
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
    start = models.DateTimeField()
    end = models.DateTimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reservations")
    comment = models.TextField(null=True, blank=True)
    accepted = models.BooleanField(default=None, null=True, blank=True)

    def clean(self):
        """Clean model."""
        super(Reservation, self).clean()
        if self.end is not None and self.start is not None and self.end <= self.start:
            raise ValidationError({"end_time": "End date cannot be before start date."})

    def __str__(self):
        """Convert this object to string."""
        if self.association:
            if self.end:
                return (
                    f"Reservation {self.title} ({self.association}, "
                    f"{self.start:%Y-%m-%d %H:%M} - {self.end:%Y-%m-%d %H:%M})"
                )
            return f"Reservation {self.title} ({self.association}, {self.start:%Y-%m-%d %H:%M})"
        if self.end:
            return f"Reservation {self.title} ({self.start:%Y-%m-%d %H:%M} - {self.end:%Y-%m-%d %H:%M})"
        return f"Reservation {self.title} ({self.start:%Y-%m-%d %H:%M})"
