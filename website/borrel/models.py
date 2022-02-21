from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from associations.models import Association
from venues.models import Reservation

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


class ProductCategory(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):

    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, related_name="products", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=6)

    def __str__(self):
        """Convert this object to string."""
        return self.name


class BorrelReservation(models.Model):
    """Borrel Reservation class."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    title = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False, related_name="borrel_reservations"
    )
    association = models.ForeignKey(
        Association, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations"
    )
    comments = models.TextField(null=True, blank=True)

    accepted = models.BooleanField(default=None, null=True, blank=True)

    venue_reservation = models.OneToOneField(
        Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations"
    )

    @property
    def submitted(self):
        return self.submitted_at is not None

    def clean(self):
        """Clean model."""
        super(BorrelReservation, self).clean()
        if self.end is not None and self.start is not None and self.end <= self.start:
            raise ValidationError({"end": "End date cannot be before start date."})
        if self.submitted_at is not None and self.start is not None and self.start <= self.submitted_at:
            raise ValidationError({"submitted_at": "Cannot be submitted before start."})

    def __str__(self):
        """Convert this object to string."""
        return "{}, {} ({} - {})".format(self.title, self.association, self.start, self.end)


class ReservationItem(models.Model):

    reservation = models.ForeignKey(BorrelReservation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(blank=True, null=True)
    product_price_per_unit = models.DecimalField(decimal_places=2, max_digits=6)
    amount_reserved = models.PositiveIntegerField()
    amount_used = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ["reservation", "product"]

    def __str__(self):
        """Convert this object to string."""
        return f"{self.product_name} for {self.product}"
