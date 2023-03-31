from django.db import models

from borrel.models import BorrelReservation
from orders.models import Shift


class SilvasoftShiftSynchronization(models.Model):
    """Model for indicating when a TOSTI Shift has been synchronized with Silvasoft."""

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class SilvasoftBorrelReservationSynchronization(models.Model):
    """Model for indicating when a TOSTI BorrelReservation has been synchronized with Silvasoft."""

    borrel_reservation = models.ForeignKey(BorrelReservation, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
