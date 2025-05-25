from django.db import models
from django.db.models import Q
from django.utils import timezone

from tinymce.models import HTMLField


class AnnouncementManager(models.Manager):
    """Announcement Manager."""

    def visible(self):
        """Get only visible announcements."""
        return self.get_queryset().filter(
            (Q(until__gt=timezone.now()) | Q(until=None)) & Q(since__lte=timezone.now())
        )


class Announcement(models.Model):
    """Announcement model."""

    title = models.CharField(
        max_length=100,
        help_text="This is not shown on the announcement but can be used as an identifier in the admin area.",
    )
    content = HTMLField(blank=False, max_length=500)
    since = models.DateTimeField(default=timezone.now)
    until = models.DateTimeField(blank=True, null=True)
    icon = models.CharField(
        verbose_name="Font Awesome 6 icon",
        help_text="Font Awesome 6 abbreviation for icon to use.",
        max_length=150,
        default="bullhorn",
    )

    objects = AnnouncementManager()

    class Meta:
        """Meta class."""

        ordering = ("-since",)

    def __str__(self):
        """Cast this object to string."""
        return self.title

    @property
    def is_visible(self):
        """Is this announcement currently visible."""
        return (
            self.until is None or self.until > timezone.now()
        ) and self.since <= timezone.now()
