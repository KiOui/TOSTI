from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class BasicBorrelBrevet(models.Model):
    """Basic Borrel Brevet class."""

    user = models.OneToOneField(
        User, blank=False, null=False, on_delete=models.CASCADE, related_name="basic_borrel_brevet"
    )
    registered_on = models.DateField(auto_now_add=True, blank=False, null=False)
    alcohol_certificate = models.FileField(null=True, blank=True)  # TODO: Add folder in which to save certificates

    @property
    def has_certificate(self):
        """Check if this BasicBorrelBrevet has a certificate registered."""
        return self.alcohol_certificate is not None

    def __str__(self):
        """Convert this object to string."""
        return self.user.__str__()
