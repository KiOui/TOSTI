from django.db import models


class Venue(models.Model):
    """Venue model class."""

    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        """Meta class."""

        ordering = ["-active", "name"]

    def __str__(self):
        """
        Convert this object to string.

        :return: the name of this Venue
        """
        return self.name
