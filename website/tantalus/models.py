from django.db import models

from orders.models import Product, OrderVenue, Shift


class TantalusProduct(models.Model):
    """Model for connecting TOSTI Products to Tantalus Products."""

    product = models.OneToOneField(Product, on_delete=models.CASCADE, blank=False, null=False)
    tantalus_id = models.PositiveIntegerField(blank=False, null=False)

    def __str__(self):
        """Convert to string."""
        return "Tantalus Product for {} with id {}".format(self.product, self.tantalus_id)


class TantalusOrderVenue(models.Model):
    """Model for connecting OrderVenue's to Tantalus Endpoints."""

    order_venue = models.OneToOneField(OrderVenue, on_delete=models.CASCADE, blank=False, null=False)
    endpoint_id = models.PositiveIntegerField(blank=False, null=False)

    def __str__(self):
        """Convert to string."""
        return "Tantalus Venue for {} with id {}".format(self.order_venue, self.endpoint_id)


class TantalusShiftSynchronization(models.Model):
    """Model for indicating whether TOSTI Shifts have been synchronized with Tantalus."""

    shift = models.OneToOneField(Shift, on_delete=models.CASCADE, blank=False, null=False)
