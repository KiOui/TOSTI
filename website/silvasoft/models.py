from django.db import models

from associations.models import Association
from borrel.models import BorrelReservation
from orders.models import Shift, Product as OrderProduct
from borrel.models import Product as BorrelProduct


class CachedRelation(models.Model):
    """
    Model for cached relation.

    We cache relations because each API call to Silvasoft is reduced from an hourly budget.
    """

    customer_number = models.IntegerField()
    name = models.CharField(max_length=100)


class CachedProduct(models.Model):
    """
    Model for cached products.

    We cache products because each API call to Silvasoft is reduced from an hourly budget.
    """

    product_number = models.CharField(max_length=100)
    name = models.CharField(max_length=100)


class SilvasoftAssociation(models.Model):
    """Model for connecting TOSTI associations to Silvasoft clients."""

    silvasoft_customer_number = models.IntegerField(unique=True)
    association = models.OneToOneField(Association, on_delete=models.CASCADE)

    def __str__(self):
        """Convert this object to string."""
        return "{} ({})".format(self.association, self.silvasoft_customer_number)


class SilvasoftOrderProduct(models.Model):
    """Model for connection TOSTI order products to Silvasoft products."""

    silvasoft_product_number = models.CharField(max_length=100, unique=True)
    product = models.OneToOneField(OrderProduct, on_delete=models.CASCADE)

    def __str__(self):
        """Convert this object to string."""
        return "{} ({})".format(self.product, self.silvasoft_product_number)


class SilvasoftBorrelProduct(models.Model):
    """Model for connection TOSTI borrel products to Silvasoft products."""

    silvasoft_product_number = models.CharField(max_length=100, unique=True)
    product = models.OneToOneField(BorrelProduct, on_delete=models.CASCADE)

    def __str__(self):
        """Convert this object to string."""
        return "{} ({})".format(self.product, self.silvasoft_product_number)


class SilvasoftShiftSynchronization(models.Model):
    """Model for indicating when a TOSTI Shift has been synchronized with Silvasoft."""

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)


class SilvasoftBorrelReservationSynchronization(models.Model):
    """Model for indicating when a TOSTI BorrelReservation has been synchronized with Silvasoft."""

    borrel_reservation = models.ForeignKey(BorrelReservation, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
