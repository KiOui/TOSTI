from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from associations.models import Association
from venues.models import Venue, Reservation

User = get_user_model()


class BasicBorrelBrevet(models.Model):
    """Basic Borrel Brevet class."""

    user = models.OneToOneField(
        User, blank=False, null=False, on_delete=models.CASCADE, related_name="basic_borrel_brevet"
    )
    registered_on = models.DateField(auto_now_add=True, blank=False, null=False)

    def __str__(self):
        """Convert this object to string."""
        return self.user.__str__()


class ReservationRequest(models.Model):
    """Reservation Request class."""

    title = models.CharField(max_length=100, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservation_requests")
    association = models.ForeignKey(
        Association, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservation_requests"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reservation_requests")
    comment = models.TextField(null=True, blank=True)
    accepted = models.BooleanField(default=None, null=True, blank=True)
    reservation = models.OneToOneField(Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservation_request")

    def clean(self):
        """Clean model."""
        super(ReservationRequest, self).clean()
        if self.end_time is not None and self.start_time is not None and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "End date cannot be before start date."})

    def __str__(self):
        """Convert this object to string."""
        return "{}, {} ({} - {})".format(self.title, self.venue, self.start_time, self.end_time)


class BorrelForm(models.Model):
    """Borrel Form class."""

    pass
