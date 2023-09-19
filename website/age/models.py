from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class AgeRegistration(models.Model):
    """Class to save an age registration."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="is_18_years_old")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    minimum_age = models.PositiveIntegerField()

    def __str__(self):
        """Convert this object to string."""
        return f"{self.user} ({self.created_at})"
