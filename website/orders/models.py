from datetime import datetime
from decimal import Decimal

from django.conf import settings
import pytz
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from venues.models import Venue

User = get_user_model()


class Product(models.Model):
    """Products that can be ordered."""

    name = models.CharField(max_length=50, unique=True, null=False, blank=False)
    icon = models.CharField(
        max_length=20,
        unique=True,
        help_text="Font-awesome icon name that is used for quick display of the product type.",
    )
    available = models.BooleanField(default=True, null=False)
    available_at = models.ManyToManyField(Venue)

    current_price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    max_allowed_per_shift = models.PositiveSmallIntegerField(
        verbose_name="Max. allowed orders per shift",
        default=2,
        null=True,
        blank=True,
        help_text="The maximum amount a single user can order this product in a single shift. Note that shifts are bound to the venue. Empty means no limit.",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-available", "name"]


class Shift(models.Model):
    """Shifts in which orders can be placed."""

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M"

    venue = models.ForeignKey(Venue, blank=False, null=False, on_delete=models.PROTECT)

    start_date = models.DateTimeField(blank=False, null=False, default=datetime.now().replace(hour=12, minute=15, second=0, microsecond=0))
    end_date = models.DateTimeField(blank=False, null=False, default=datetime.now().replace(hour=13, minute=15,  second=0, microsecond=0))

    orders_allowed = models.BooleanField(verbose_name="Orders allowed", default=False, blank=False, null=False, help_text="If checked, people can order within the given time frame. If not checked, ordering will not be possible, even in the given time frame.")

    max_orders_per_user = models.PositiveSmallIntegerField(
        verbose_name="Max. number of orders per user",
        default=2,
        null=True,
        blank=True,
        help_text="The maximum amount of products a single user can order in this shift. Empty means no limit.",
    )

    max_orders_total = models.PositiveSmallIntegerField(
        verbose_name="Max. total number of orders",
        default=50,
        null=True,
        blank=True,
        help_text="The maximum amount of products that can be ordered during this shift in total. Empty means no limit.",
    )

    assignees = models.ManyToManyField(User)

    @property
    def number_of_orders(self):
        return Order.objects.filter(shift=self).count()

    @property
    def max_orders_total_string(self):
        if self.max_orders_total:
            return self.max_orders_total
        return "∞"

    @property
    def capacity(self):
        return f"{self.number_of_orders} / {self.max_orders_total_string}"

    @property
    def can_order(self):
        return self.orders_allowed and (
            self.number_of_orders < self.max_orders_total or not self.max_orders_total
        )

    @property
    def is_active(self):
        timezone = pytz.timezone(settings.TIME_ZONE)
        current_time = timezone.localize(datetime.now())
        return self.start_date < current_time < self.end_date

    @property
    def date(self):
        if self.start_date.date() == self.end_date.date():
            return f"{self.start_date.strftime(self.DATE_FORMAT)}"
        return f"{self.start_date.strftime(self.DATE_FORMAT)} - {self.end_date.strftime(self.DATE_FORMAT)}"

    @property
    def start_time(self):
        return f"{self.start_date.strftime(self.TIME_FORMAT)}"

    @property
    def end_time(self):
        return f"{self.end_date.strftime(self.TIME_FORMAT)}"

    def __str__(self):
        return f"Shift {self.venue} {self.date}"

    def save(self, *args, **kwargs):
        if not self.venue.active:
            raise ValueError(f"This venue is currently not active.")

        overlapping_start = (
            Shift.objects.filter(
                start_date__gte=self.start_date,
                start_date__lte=self.end_date,
                venue=self.venue,
            )
            .exclude(pk=self.pk)
            .count()
        )
        overlapping_end = (
            Shift.objects.filter(
                end_date__gte=self.start_date,
                end_date__lte=self.end_date,
                venue=self.venue,
            )
            .exclude(pk=self.pk)
            .count()
        )
        if overlapping_start > 0 or overlapping_end > 0:
            raise ValueError("Overlapping shifts for the same venue are not allowed.")

        super(Shift, self).save(*args, **kwargs)

    class Meta:
        ordering = ["start_date", "end_date"]


class Order(models.Model):
    """
    A user that ordered a product.

    Orders only contain a single product. If a user orders multiple products
    (or multiple amounts of products) he or she must place multiple orders.
    Verifying the amount of allowed orders is done via Shifts.
    """

    created = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.PROTECT)
    shift = models.ForeignKey(Shift, blank=False, null=False, on_delete=models.PROTECT)
    product = models.ForeignKey(
        Product, blank=False, null=False, on_delete=models.PROTECT
    )

    order_price = models.DecimalField(max_digits=6, decimal_places=2)

    paid = models.BooleanField(default=False, null=False)
    delivered = models.BooleanField(default=False, null=False)

    def __str__(self):
        return f"{self.product} for {self.user} ({self.shift})"

    def save(self, *args, **kwargs):
        if not self.shift.can_order:
            raise ValueError(f"You cannot order for this shift right now.")
        if not self.product.available:
            raise ValueError(f"This product is not available right now.")
        if (
            self.shift.max_orders_per_user is not None
            and Order.objects.filter(shift=self.shift).exclude(pk=self.pk).count()
            >= self.shift.max_orders_per_user
        ):
            raise ValueError(
                f"You are not allowed to order more than {self.shift.max_orders_per_user} products in this shift."
            )
        if (
            self.product.max_allowed_per_shift is not None
            and Order.objects.filter(product=self.product).exclude(pk=self.pk).count()
            >= self.product.max_allowed_per_shift
        ):
            raise ValueError(
                f"You are not allowed to order more than {self.product.max_allowed_per_shift} products of this kind in this shift."
            )

        self.order_price = self.product.current_price

        super(Order, self).save(*args, **kwargs)

    @property
    def get_venue(self):
        return self.shift.venue

    class Meta:
        ordering = ["created"]
