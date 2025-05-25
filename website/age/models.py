from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class AgeRegistration(models.Model):
    """Class to save an age registration."""

    YIVI = "yivi"
    MANUAL = "manual"
    VERIFIED_BY_CHOICES = (
        (YIVI, "Yivi"),
        (MANUAL, "Manually"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="is_18_years_old"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    minimum_age = models.PositiveIntegerField()

    verified_by = models.CharField(
        max_length=100, null=True, blank=True, choices=VERIFIED_BY_CHOICES
    )
    attributes = models.JSONField(max_length=1000, null=True, blank=True)
    verified_by_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        """Convert this object to string."""
        return f"{self.user} ({self.created_at})"
