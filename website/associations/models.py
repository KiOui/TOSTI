from django.db import models


class Association(models.Model):
    """Association model."""

    name = models.CharField(max_length=150)

    def __str__(self):
        """Convert this object to string."""
        return self.name
