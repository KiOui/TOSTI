from django.db import models

from orders.models import Product


class TantalusProduct(models.Model):
    """Model for connecting TOSTI Products to Tantalus Products."""

    product = models.OneToOneField(Product, on_delete=models.CASCADE, blank=False, null=False)
    tantalus_id = models.PositiveIntegerField(blank=False, null=False)

    def __str__(self):
        """Convert to string."""
        return "Tantalus Product for {} with id {}".format(self.product, self.tantalus_id)
