from datetime import datetime
from decimal import Decimal

from django.conf import settings
import pytz
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from guardian.shortcuts import get_objects_for_user

from associations.models import Association
from venues.models import Venue
from itertools import chain

from users.models import User


def validate_barcode(value):
    """
    Validate a barcode.

    Checks if the barcode is all digits, of the required length and if the checksum is correct
    :param value: the value to validate
    :return: None, raises ValidationError if a check fails
    """
    if value is None:
        return

    if not value.isdigit():
        raise ValidationError("A barcode must consist of only digits")

    if len(value) == 8:
        value = "000000" + value
    elif len(value) == 13:
        value = "0" + value
    else:
        raise ValidationError("A barcode must be either 8 or 13 integers long")

    counter = 0
    for index, digit in enumerate(value[: len(value) - 1]):
        if index % 2 == 0:
            counter += int(digit) * 3
        else:
            counter += int(digit)

    if (10 - (counter % 10)) % 10 != int(value[len(value) - 1]):
        raise ValidationError("The checksum of the barcode is not correct")


def get_default_start_time_shift():
    """
    Get the default start time of a Shift object.

    :return: the default start time of a shift
    """
    timezone = pytz.timezone(settings.TIME_ZONE)
    return timezone.localize(datetime.now()).replace(hour=12, minute=15, second=0, microsecond=0)


def get_default_end_time_shift():
    """
    Get the default end time of a Shift object.

    :return: the default end time of a shift
    """
    timezone = pytz.timezone(settings.TIME_ZONE)
    return timezone.localize(datetime.now()).replace(hour=13, minute=15, second=0, microsecond=0)


class OrderVenue(models.Model):
    """Venues where Shifts can be created."""

    venue = models.OneToOneField(
        Venue,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    class Meta:
        """Meta class for OrderVenue."""

        ordering = ["venue__name"]

        permissions = [
            ("can_order_in_venue", "Can order products during shifts in this venue"),
            ("can_manage_shift_in_venue", "Can manage shifts in this venue"),
        ]

    def __str__(self):
        """Representation by venue."""
        return str(self.venue)

    def get_users_with_shift_admin_perms(self):
        """Get users with permissions to manage shifts in this venue."""
        users = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "orders.can_manage_shift_in_venue", accept_global_perms=True, with_superuser=True
            ):
                users.append(user)
        return users

    def get_users_with_shift_admin_perms_queryset(self):
        """Get users with permissions to manage shifts in this venue as queryset."""
        users_ids = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "orders.can_manage_shift_in_venue", accept_global_perms=True, with_superuser=True
            ):
                users_ids.append(user.pk)
        return User.objects.filter(pk__in=users_ids)

    def get_users_with_order_perms(self):
        """Get users with permissions to manage shifts in this venue."""
        users = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "orders.can_order_in_venue", accept_global_perms=True, with_superuser=True
            ):
                users.append(user)
        return users

    def get_users_with_order_perms_queryset(self):
        """Get users with permissions to manage shifts in this venue as queryset."""
        users_ids = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "orders.can_order_in_venue", accept_global_perms=True, with_superuser=True
            ):
                users_ids.append(user.pk)
        return User.objects.filter(pk__in=users_ids)


class Product(models.Model):
    """Products that can be ordered."""

    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(
        max_length=20,
        default="",
        blank=True,
        help_text=("Font-awesome icon name that is used for quick display of the product type."),
    )
    available = models.BooleanField(default=True)
    available_at = models.ManyToManyField(OrderVenue)

    current_price = models.DecimalField(
        max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    orderable = models.BooleanField(
        default=True,
        help_text="Whether or not this product should appear on the order page.",
    )
    ignore_shift_restrictions = models.BooleanField(
        default=False,
        help_text="Whether or not this product should ignore the maximum orders per shift" " restriction.",
    )

    max_allowed_per_shift = models.PositiveSmallIntegerField(
        verbose_name="Max. allowed orders per shift",
        default=2,
        null=True,
        blank=True,
        help_text="The maximum amount a single user can order this product in a single shift. Note that shifts are "
        "bound to the venue. Empty means no limit.",
    )

    barcode = models.CharField(
        max_length=13,
        default=None,
        null=True,
        blank=True,
        unique=True,
        help_text="Either an EAN-8 or EAN-13 barcode.",
        validators=[validate_barcode],
    )

    class Meta:
        """Meta class."""

        ordering = ["-available", "name"]

    def __str__(self):
        """
        Convert a Product object to string.

        :return: the name of the Product object
        """
        return self.name

    def to_json(self):
        """
        Convert this object to JSON.

        :return: a to JSON convertable dictionary of properties.
        """
        return {
            "name": self.name,
            "icon": self.icon,
            "price": self.current_price,
            "max_per_shift": self.max_allowed_per_shift,
            "available": self.available,
            "id": self.pk,
            "ignore_shift_restriction": self.ignore_shift_restrictions,
        }

    def user_can_order_amount(self, user, shift, amount=1):
        """
        Test if a user can order the specified amount of this Product in a specific shift.

        :param user: the user
        :param shift: the shift
        :param amount: the amount that the user wants to order
        :return: True if the already ordered amount of this Product plus the amount specified in the amount parameter
        is lower than the max_allowed_per_shift variable, False otherwise
        """
        if self.max_allowed_per_shift is not None:
            user_order_amount_product = Order.objects.filter(user=user, shift=shift, product=self).count()
            return user_order_amount_product + amount <= self.max_allowed_per_shift
        return True

    def user_max_order_amount(self, user, shift):
        """
        Get the maximum amount a user can still order for this product.

        :param user: the user
        :param shift: the shift on which to order the product
        :return: None if the user can order unlimited of the product, the maximum allowed to still order otherwise
        """
        if self.max_allowed_per_shift is not None:
            if not user.is_authenticated:
                return 0  # Non logged-in users can never order items
            user_order_amount_product = Order.objects.filter(user=user, shift=shift, product=self).count()
            return max(0, self.max_allowed_per_shift - user_order_amount_product)
        else:
            return None


def active_venue_validator(value):
    """Filter to only allow shifts for active venues."""
    if OrderVenue.objects.get(pk=value).venue.active:
        return True
    else:
        raise ValidationError("This venue is not active.")


class Shift(models.Model):
    """Shifts in which orders can be placed."""

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M"
    HUMAN_DATE_FORMAT = "%a. %-d %b. %Y"

    venue = models.ForeignKey(
        OrderVenue, related_name="shifts", on_delete=models.PROTECT, validators=[active_venue_validator]
    )

    start_date = models.DateTimeField(default=get_default_start_time_shift)
    end_date = models.DateTimeField(default=get_default_end_time_shift)

    can_order = models.BooleanField(
        verbose_name="Orders allowed",
        default=False,
        help_text=(
            "If checked, people can order within the given time frame. If not checked,"
            " ordering will not be possible, even in the given time frame."
        ),
    )

    finalized = models.BooleanField(
        verbose_name="Shift Finalized",
        default=False,
        help_text="If checked, shift is finalized and no alterations on the shift can be made anymore.",
    )

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
        help_text="The maximum amount of products that can be ordered during this shift in total. Empty means no "
        "limit.",
    )

    assignees = models.ManyToManyField(User)

    class Meta:
        """Meta class."""

        ordering = ["start_date", "end_date"]

    def __str__(self):
        """
        Convert this object to string.

        :return: this object in string format
        """
        return f"{self.venue} {self.date}"

    def save(self, *args, **kwargs):
        """Save a Shift."""
        self._clean()
        try:
            old_instance = Shift.objects.get(id=self.id)
        except Shift.DoesNotExist:
            old_instance = None

        if old_instance is not None and not old_instance.finalized and self.finalized:
            # Shift was not finalized yet but will be made finalized now
            self._make_finalized()

        return super(Shift, self).save(*args, **kwargs)

    @property
    def orders_sorted_staff_first(self):
        """
        Get the orders of this shift with the staff orders first.

        :return: a chain object with all the orders of this shift.
        """
        staff_users = self.venue.get_users_with_shift_admin_perms()
        ordered_staff_orders = Order.objects.filter(shift=self, user__in=staff_users).order_by("created")
        ordered_normal_orders = Order.objects.filter(shift=self).exclude(user__in=staff_users).order_by("created")
        ordered_orders = chain(ordered_staff_orders, ordered_normal_orders)
        return list(ordered_orders)

    @property
    def orders_ordered_type_only(self):
        """
        Get the orders with type Ordered of this shift.

        :return: a chain object with the ordered orders of this shift.
        """
        staff_users = self.venue.get_users_with_shift_admin_perms()
        ordered_staff_orders = Order.objects.filter(
            shift=self, user__in=staff_users, type=Order.TYPE_ORDERED
        ).order_by("created")
        ordered_normal_orders = (
            Order.objects.filter(shift=self, type=Order.TYPE_ORDERED).exclude(user__in=staff_users).order_by("created")
        )
        ordered_orders = chain(ordered_staff_orders, ordered_normal_orders)
        return list(ordered_orders)

    @property
    def products_open(self):
        """
        Get a list with all products and amounts that are not ready.

        :return: a list of products with a amount object variable indicating the products and amounts that are not
        ready for this shift
        """
        distinct_ordered_items = Product.objects.filter(order__shift_id=self, order__ready=False).distinct()
        for item in distinct_ordered_items:
            item.amount = Order.objects.filter(product=item, ready=False, shift=self).count()
        return distinct_ordered_items

    @property
    def products_closed(self):
        """
        Get a list with all products and amounts that are ready.

        :return: a list of products with a amount object variable indicating the products and amounts that are ready
        for this shift
        """
        distinct_ordered_items = Product.objects.filter(order__shift_id=self, order__ready=True).distinct()
        for item in distinct_ordered_items:
            item.amount = Order.objects.filter(product=item, ready=True, shift=self).count()
        return distinct_ordered_items

    @property
    def products_total(self):
        """
        Get a list with all products and amounts.

        :return: a list of products with a amount object variable indicating the products and amounts for this shift
        """
        distinct_ordered_items = Product.objects.filter(order__shift_id=self).distinct()
        for item in distinct_ordered_items:
            item.amount = Order.objects.filter(product=item, shift=self).count()
        return distinct_ordered_items

    @property
    def number_of_orders(self):
        """
        Get the total number of orders in this shift.

        :return: the total number of orders in this shift
        """
        return Order.objects.filter(shift=self).count()

    @property
    def max_orders_total_string(self):
        """
        Get the maximum amount of orders in string format.

        :return: the maximum amount of orders in string format
        """
        if self.max_orders_total:
            return self.max_orders_total
        return "∞"

    @property
    def capacity(self):
        """
        Get the current capacity of a shift as a string.

        :return: the current capacity of a shift in string format
        """
        return f"{self.number_of_orders} / {self.max_orders_total_string}"

    @property
    def is_active(self):
        """
        Check if a shift is currently active.

        :return: True if the current time is between the start_date and end_date of this shift
        """
        timezone = pytz.timezone(settings.TIME_ZONE)
        current_time = timezone.localize(datetime.now())
        return self.start_date < current_time < self.end_date

    @property
    def date(self):
        """
        Get the date of this object in string format.

        :return: the date of this object in string format
        """
        if self.start_date.date() == self.end_date.date():
            return f"{self.start_date.strftime(self.DATE_FORMAT)}"
        return f"{self.start_date.strftime(self.DATE_FORMAT)} - {self.end_date.strftime(self.DATE_FORMAT)}"

    @property
    def start_time(self):
        """
        Get the start time of this object in string format.

        :return: the start time of this object in string format
        """
        timezone = pytz.timezone(settings.TIME_ZONE)
        localized = datetime.fromtimestamp(self.start_date.timestamp(), tz=timezone)
        return f"{localized.strftime(self.TIME_FORMAT)}"

    @property
    def end_time(self):
        """
        Get the end time of this object in string format.

        :return: the end time of this object in string format
        """
        timezone = pytz.timezone(settings.TIME_ZONE)
        localized = datetime.fromtimestamp(self.end_date.timestamp(), tz=timezone)
        return f"{localized.strftime(self.TIME_FORMAT)}"

    @property
    def human_readable_start_end_time(self):
        """Get the start and and time in a human readable format."""
        timezone = pytz.timezone(settings.TIME_ZONE)
        start_time = datetime.fromtimestamp(self.start_date.timestamp(), tz=timezone)
        end_date = datetime.fromtimestamp(self.end_date.timestamp(), tz=timezone)

        if start_time.date() == end_date.date():
            if start_time.date() == datetime.today().date():
                return f"{self.start_time} until {self.end_time}"
            return f"{self.start_date.strftime(self.HUMAN_DATE_FORMAT)}, {self.start_time} until {self.end_time}"
        if start_time.date() == datetime.today().date():
            return f"{self.start_time} until {self.end_date.strftime(self.HUMAN_DATE_FORMAT)}, {self.end_time}"
        return (
            f"{self.start_date.strftime(self.HUMAN_DATE_FORMAT)}, {self.start_time} until "
            f"{self.end_date.strftime(self.HUMAN_DATE_FORMAT)}, {self.end_time}"
        )

    def get_assignees(self):
        """
        Get assignees of this shift.

        :return: a QuerySet with User objects of assignees of this shift
        """
        return self.assignees.all()

    def get_users_with_change_perms(self):
        """Get users that my change this shift."""
        users = []
        for user in User.objects.all():
            if self in get_objects_for_user(
                user, "orders.change_shift", accept_global_perms=True, with_superuser=True
            ):
                users.append(user)
        return users

    def _make_finalized(self):
        """Make this Shift ready to be finalized."""
        timezone = pytz.timezone(settings.TIME_ZONE)
        self.end_date = timezone.localize(datetime.now())
        self.can_order = False

    @property
    def shift_done(self):
        """
        Check if all Orders of this Shift are ready and paid.

        :return: True if all Orders (with the Order type) of this Shift are ready and paid, False otherwise
        :rtype: boolean
        """
        return False not in [x.done for x in self.orders_sorted_staff_first if x.type != Order.TYPE_SCANNED]

    def _clean(self):
        """
        Check the configuration of a Shift on clean or save.

        :return: None, raises a ValidationError on error
        """
        try:
            old_instance = Shift.objects.get(id=self.id)
        except Shift.DoesNotExist:
            old_instance = None

        if old_instance is not None and old_instance.finalized and not self.finalized:
            # Shift was already finalized so can't be un-finalized
            raise ValidationError({"finalized": "A finalized shift can not be un-finalized."})
        elif old_instance is not None and old_instance.finalized and self.finalized:
            # Shift was already finalized and is still finalized but something else changed
            raise ValidationError("A finalized shift can not be changed")
        elif old_instance is not None and not old_instance.finalized and self.finalized:
            # Shift was not finalized yet but will be made finalized now
            if not self.shift_done:
                raise ValidationError({"finalized": "Shift can't be finalized if not all Orders are paid and ready"})

        if self.end_date <= self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

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
            raise ValidationError("Overlapping shifts for the same venue are not allowed.")

    def clean(self):
        """Clean a Shift."""
        self._clean()
        return super(Shift, self).clean()

    def save_m2m(self):
        """Save assignees m2m."""
        for assignee in self.assignees.all():
            if assignee not in self.venue.get_users_with_shift_admin_perms():
                raise ValueError(f"{assignee} is not allowed to manage this shift.")

    def user_can_order_amount(self, user, amount=1):
        """
        Test if a user can order a specific amount of products.

        :param user: the user
        :param amount: the amount that the user wants to order
        :return: True if the user is allowed to order amount of products, False otherwise
        """
        if self.max_orders_per_user is not None:
            user_order_amount = Order.objects.filter(
                user=user, shift=self, product__ignore_shift_restrictions=False
            ).count()
            return user_order_amount + amount <= self.max_orders_per_user

        return True

    def user_max_order_amount(self, user):
        """
        Get the maximum a user can still order in this shift.

        :param user: the user
        :return: the maximum of orders a user can still place in this shift, None if there is no maximum specified
        """
        if self.max_orders_per_user is not None:
            if not user.is_authenticated:
                return 0  # Non logged-in users can never order items
            user_order_amount = Order.objects.filter(
                user=user, shift=self, product__ignore_shift_restrictions=False
            ).count()
            return max(0, self.max_orders_per_user - user_order_amount)
        else:
            return None


def available_product_filter(value):
    """Filter to only allow ordering available products."""
    if type(value) == int and Product.objects.get(pk=value).available:
        return True
    elif type(value) == Product and value.available:
        return True
    else:
        raise ValidationError("This product is not available.")


class Order(models.Model):
    """
    A user that ordered a product.

    Orders only contain a single product. If a user orders multiple products
    (or multiple amounts of products) he or she must place multiple orders.
    Verifying the amount of allowed orders is done via Shifts.
    """

    TYPE_ORDERED = 0
    TYPE_SCANNED = 1
    TYPES = ((TYPE_ORDERED, "Ordered"), (TYPE_SCANNED, "Scanned"))

    created = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, related_name="orders", blank=True, null=True, on_delete=models.PROTECT)
    user_association = models.ForeignKey(
        Association, related_name="orders", blank=True, null=True, on_delete=models.SET_NULL
    )
    shift = models.ForeignKey(Shift, related_name="orders", on_delete=models.PROTECT)
    product = models.ForeignKey(
        Product, related_name="orders", on_delete=models.PROTECT, validators=[available_product_filter]
    )

    order_price = models.DecimalField(max_digits=6, decimal_places=2)

    ready = models.BooleanField(default=False)
    ready_at = models.DateTimeField(null=True, blank=True)

    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    type = models.PositiveIntegerField(choices=TYPES, default=0)

    class Meta:
        """Meta class."""

        ordering = ["created"]

    def __str__(self):
        """
        Convert this object to string.

        :return: string format of this object
        """
        return f"{self.product} for {self.user} ({self.shift})"

    def save(self, *args, **kwargs):
        """
        Save an object of the Order type.

        :param args: arguments
        :param kwargs: keyword arguments
        :return: an instance of the Order object if the saving succeeded, raises a ValueError on error
        """
        if not self.order_price:
            self.order_price = self.product.current_price

        super(Order, self).save(*args, **kwargs)

    def to_json(self):
        """
        Convert this object to JSON.

        :return: a to JSON convertable dictionary of properties.
        """
        return {
            "id": self.pk,
            "user": self.user.username,
            "product": self.product.to_json(),
            "price": self.order_price,
            "paid": self.paid,
            "ready": self.ready,
        }

    def clean(self):
        """
        Clean this Order.

        Check if the Shift is already finalized.
        """
        super().clean()
        if self.shift.finalized:
            raise ValidationError("Order can't be changed as Shift is already finalized")

    @property
    def get_venue(self):
        """
        Get the venue of this Order.

        :return: the venue associated to this Order
        """
        return self.shift.venue

    @property
    def done(self):
        """
        Check if an Order is done.

        :return: True if this Order is paid and ready, False otherwise
        :rtype: boolean
        """
        return self.paid and self.ready
