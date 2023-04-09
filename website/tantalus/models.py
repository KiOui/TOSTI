from django.db import models

from orders.models import Product as OrdersProduct, OrderVenue, Shift
from borrel.models import Product as BorrelProduct, BorrelReservation
from associations.models import Association


class TantalusShiftSynchronization(models.Model):
    """Model for indicating whether TOSTI Shifts have been synchronized with Tantalus."""

    shift = models.OneToOneField(Shift, on_delete=models.CASCADE)


class TantalusBorrelReservationSynchronization(models.Model):
    """Model for indicating whether TOSTI BorrelReservations have been synchronized with Tantalus."""

    borrel_reservation = models.OneToOneField(BorrelReservation, on_delete=models.CASCADE)

