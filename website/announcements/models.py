from django.db import models
from django.utils import timezone

from tinymce.models import HTMLField


class Announcement(models.Model):
    """Announcement model."""

    title = models.CharField(max_length=100, help_text="This is not showed on the announcement but can be used as an identifier in the admin area.")
    content = HTMLField(blank=False, max_length=500)
    since = models.DateTimeField(default=timezone.now)
    until = models.DateTimeField(blank=True, null=True)
    icon = models.CharField(
        verbose_name="Font Awesome icon",
        help_text="Font Awesome abbreviation for icon to use.",
        max_length=150,
        default="bullhorn",
    )

    class Meta:
        """Meta class."""

        ordering = ("-since",)

    def __str__(self):
        """Cast this object to string."""
        return self.title

    @property
    def is_visible(self):
        """Is this announcement currently visible."""
        return (self.until is None or self.until > timezone.now()) and self.since <= timezone.now()
