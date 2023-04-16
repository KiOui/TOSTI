from django.db import models

from orders.models import Shift
from borrel.models import BorrelReservation


class TantalusShiftSynchronization(models.Model):
    """Model for indicating whether TOSTI Shifts have been synchronized with Tantalus."""

    shift = models.OneToOneField(Shift, on_delete=models.CASCADE)


class TantalusBorrelReservationSynchronization(models.Model):
    """Model for indicating whether TOSTI BorrelReservations have been synchronized with Tantalus."""

    borrel_reservation = models.OneToOneField(BorrelReservation, on_delete=models.CASCADE)
