import secrets
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from queryable_properties.managers import QueryablePropertiesManager
from queryable_properties.properties import RangeCheckProperty

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    title = models.CharField(max_length=100, null=False, blank=False)
    association = models.ForeignKey(
        Association, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations"
    )
    start = models.DateTimeField()
    end = models.DateTimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reservations")
    user_created = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations_created"
    )
    user_updated = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations_updated"
    )
    users_access = models.ManyToManyField(User, related_name="reservations_access", blank=True)

    comments = models.TextField(null=True, blank=True)

    accepted = models.BooleanField(default=None, null=True, blank=True)
    join_code = models.CharField(
        max_length=255, blank=True, null=True, unique=True, validators=[MinLengthValidator(20)]
    )

    active = RangeCheckProperty("start", "end", timezone.now)

    objects = QueryablePropertiesManager()

    @property
    def can_be_changed(self):
        return self.accepted is None and self.start > timezone.now()

    def clean(self):
        """Clean model."""
        super(Reservation, self).clean()
        if self.end is not None and self.start is not None and self.end <= self.start:
            raise ValidationError({"end_time": "End date cannot be before start date."})

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save the reservation."""
        if not self.join_code:
            self.join_code = secrets.token_urlsafe(20)

        super().save(force_insert, force_update, using, update_fields)

        if self.user_created and self.user_created not in self.users_access.all():
            self.users_access.add(self.user_created)

    def __str__(self):
        """Convert this object to string."""
        if self.association:
            return (
                f"Reservation {self.venue} - {self.title} ({self.association}, "
                f"{self.start:%Y-%m-%d %H:%M} - {self.end:%Y-%m-%d %H:%M})"
            )
        return f"Reservation {self.venue} - {self.title} ({self.start:%Y-%m-%d %H:%M} - {self.end:%Y-%m-%d %H:%M})"

    class Meta:
        """Meta class."""

        ordering = ["-start", "-end", "title"]
