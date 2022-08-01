import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

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
        return f"Borrel brevet for {self.user}"


class ProductCategory(models.Model):
    """Product category model."""

    name = models.CharField(max_length=100)

    def __str__(self):
        """Convert this object to string."""
        return self.name

    def __le__(self, other):
        """Compare categories for ordering."""
        return self.pk <= other.pk

    class Meta:
        """Meta class for model."""

        verbose_name = "product category"
        verbose_name_plural = "product categories"


class ProductQuerySet(models.QuerySet):
    """Product queryset."""

    def available(self):
        """Only available products."""
        return self.filter(active=True)


class ProductManager(models.Manager):
    """Custom manager for products."""

    def get_queryset(self):
        """Get product queryset."""
        return ProductQuerySet(self.model, using=self._db)

    def available_products(self):
        """Only available products."""
        return self.get_queryset().available()


class Product(models.Model):
    """Product model."""

    objects = ProductManager()

    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, related_name="products", null=True, blank=True
    )
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
    end = models.DateTimeField(null=True, blank=True)
    user_created = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations_created"
    )
    user_updated = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations_updated"
    )
    user_submitted = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations_submitted"
    )
    users_access = models.ManyToManyField(User, related_name="borrel_reservations_access", blank=True)

    association = models.ForeignKey(
        Association, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations"
    )
    comments = models.TextField(null=True, blank=True)

    accepted = models.BooleanField(default=None, null=True, blank=True)

    venue_reservation = models.OneToOneField(
        Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrel_reservations"
    )

    join_code = models.UUIDField(null=False, blank=True, unique=True)

    @property
    def submitted(self):
        """Borrel reservation is submitted."""
        return self.submitted_at is not None

    @property
    def can_be_changed(self):
        """Borrel reservation can be changed by users."""
        return self.accepted is None and not self.submitted  # this last case should not happen in practice

    @property
    def can_be_submitted(self):
        """Borrel reservation can be submitted."""
        return self.accepted and timezone.now() > self.start and not self.submitted

    def clean(self):
        """Clean model."""
        super(BorrelReservation, self).clean()
        if self.end is not None and self.start is not None and self.end <= self.start:
            raise ValidationError({"end": "End date cannot be before start date."})
        if self.submitted_at is not None and self.start is not None and self.start <= self.submitted_at:
            raise ValidationError({"submitted_at": "Cannot be submitted before start."})
        if self.user_submitted is not None and self.submitted_at is None:
            raise ValidationError({"user_submitted": "Cannot have a user submitted if not submitted."})

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save the reservation."""
        if not self.join_code:
            self.join_code = uuid.uuid4()

        super().save(force_insert, force_update, using, update_fields)

        if self.user_created and self.user_created not in self.users_access.all():
            self.users_access.add(self.user_created)

    def __str__(self):
        """Convert this object to string."""
        if self.association:
            if self.end:
                return (
                    f"Borrel reservation {self.title} ({self.association}, "
                    f"{self.start:%Y-%m-%d %H:%M} - {self.end:%Y-%m-%d %H:%M})"
                )
            return f"Borrel reservation {self.title} ({self.association}, {self.start:%Y-%m-%d %H:%M})"
        if self.end:
            return f"Borrel reservation {self.title} ({self.start:%Y-%m-%d %H:%M} - {self.end:%Y-%m-%d %H:%M})"
        return f"Borrel reservation {self.title} ({self.start:%Y-%m-%d %H:%M})"

    class Meta:
        """Meta class."""

        ordering = ["-start", "-end", "title"]


class ReservationItem(models.Model):
    """Reservation items model."""

    reservation = models.ForeignKey(BorrelReservation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(blank=True, null=True)
    product_price_per_unit = models.DecimalField(decimal_places=2, max_digits=6)
    amount_reserved = models.PositiveIntegerField()
    amount_used = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        """Meta class for the model."""

        unique_together = ["reservation", "product_name"]

    def __str__(self):
        """Convert this object to string."""
        return f"{self.product_name} for {self.reservation}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save reservation item."""
        if self.amount_reserved == 0 and (self.amount_used is None or self.amount_used == 0):
            if self.pk:
                self.delete()
            return

        if not self.product_price_per_unit:
            self.product_price_per_unit = self.product.price
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_description:
            self.product_description = self.product.description

        if self.amount_used and self.amount_used > 0 and not self.amount_reserved:
            self.amount_reserved = 0

        super().save(force_insert, force_update, using, update_fields)

        self.reservation.updated_at = timezone.now()
        self.reservation.save()
