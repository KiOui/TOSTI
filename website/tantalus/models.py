from django.db import models

from orders.models import Product as OrdersProduct, OrderVenue, Shift
from borrel.models import Product as BorrelProduct


class TantalusOrdersProduct(models.Model):
    """Model for connecting Orders Products to Tantalus Products."""

    product = models.OneToOneField(OrdersProduct, on_delete=models.CASCADE)
    tantalus_id = models.PositiveIntegerField()

    def __str__(self):
        """Convert to string."""
        return "Tantalus Product for {} with id {}".format(self.product, self.tantalus_id)


class TantalusOrderVenue(models.Model):
    """Model for connecting OrderVenue's to Tantalus Endpoints."""

    order_venue = models.OneToOneField(OrderVenue, on_delete=models.CASCADE)
    endpoint_id = models.PositiveIntegerField()

    def __str__(self):
        """Convert to string."""
        return "Tantalus Venue for {} with id {}".format(self.order_venue, self.endpoint_id)


class TantalusShiftSynchronization(models.Model):
    """Model for indicating whether TOSTI Shifts have been synchronized with Tantalus."""

    shift = models.OneToOneField(Shift, on_delete=models.CASCADE)


class TantalusBorrelProduct(models.Model):
    """Model for connecting Borrel Products to Tantalus Products."""

    product = models.OneToOneField(BorrelProduct, on_delete=models.CASCADE)
    tantalus_id = models.PositiveIntegerField()

    def __str__(self):
        """Convert to string."""
        return "Tantalus Product for {} with id {}".format(self.product, self.tantalus_id)
