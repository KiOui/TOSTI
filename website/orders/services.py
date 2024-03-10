import datetime
import logging

from django.db.models import Count, Q
from django.utils import timezone
from guardian.shortcuts import get_users_with_perms

from orders.exceptions import OrderException
from orders.models import Order, Product, Shift, OrderBlacklistedUser, OrderVenue
from users.models import User


logger = logging.getLogger(__name__)


def user_can_manage_shift(user, shift):
    """Return if the user can manage this shift."""
    return user_can_manage_shifts_in_venue(user, shift.venue) and user in shift.assignees.all()


def user_can_manage_shifts_in_venue(user, venue):
    """Return if the user can manage this shift."""
    return user.has_perm("orders.can_manage_shift_in_venue", venue)


def user_is_blacklisted(user):
    """Return if the user is on the blacklist."""
    return OrderBlacklistedUser.objects.filter(user=user).exists()


def user_gets_prioritized_orders(user, shift):
    """User's order get put first in the queue."""
    return (
        get_users_with_perms(
            shift.venue, only_with_perms_in=["gets_prioritized_orders_in_venue"], with_superusers=False
        )
        .filter(pk=user.pk)
        .exists()
    )


def execute_data_minimisation(dry_run=False):
    """
    Remove order history from users that is more than 31 days old.

    :param dry_run: does not really remove data if True
    :return: list of users from who data is removed
    """
    delete_before = timezone.now() - datetime.timedelta(days=31)
    orders = Order.objects.filter(created__lte=delete_before).exclude(paid=False)

    users = orders.values_list("user", flat=True).distinct()
    if not dry_run:
        orders.update(user=None)

    return users


def add_scanned_order(product: Product, shift: Shift, ready=True, paid=True, picked_up=True) -> Order:
    """
    Add a single Scanned Order (of type TYPE_SCANNED).

    :param product: A Product for which an Order has to be created
    :param shift: The shift for which the Orders have to be created
    :param ready: Whether the Order should be directly made ready
    :param paid: Whether the Order should be directly made paid
    :param picked_up: Whether the Order should be directly made picked up
    :return: The created Order
    """
    # Check if Shift is not finalized
    if shift.finalized:
        raise OrderException("Shift is finalized, no Orders can be added anymore")

    # Check Product availability
    if not product.available:
        raise OrderException("This Product is not available")

    # Check Product-Shift availability
    if shift.venue not in product.available_at.all():
        raise OrderException("This Product is not available in this Shift")

    return Order.objects.create(
        product=product,
        shift=shift,
        type=Order.TYPE_SCANNED,
        user=None,
        user_association=None,
        ready=ready,
        paid=paid,
        picked_up=picked_up,
    )


def add_user_order(
    product: Product,
    shift: Shift,
    user: User,
    priority: int = Order.PRIORITY_NORMAL,
    paid: bool = False,
    ready: bool = False,
    picked_up: bool = False,
    **kwargs,
) -> Order:
    """
    Add a single Order (of type TYPE_ORDERED).

    :param product: A Product for which an Order has to be created
    :param shift: The shift for which the Orders have to be created
    :param user: The User for which the Orders have to be created
    :param priority: Which priority the Order should have
    :param paid: Whether the order should be set as paid
    :param ready: Whether the order should be set as ready
    :param picked_up: Whether the order should be set as picked up
    :return: The created Order
    """
    # Check order permissions
    if user_is_blacklisted(user):
        raise OrderException("User is blacklisted")

    # Check if Shift is not finalized
    if shift.finalized:
        raise OrderException("Shift is finalized, no Orders can be added anymore")

    # Check if Shift is active
    if not shift.is_active:
        raise OrderException("Shift is not active")

    # Check if Shift is not closed
    if not shift.can_order:
        raise OrderException("This Shift is closed")

    # Check Shift order maximum while ignoring Products without Shift restrictions
    if not product.ignore_shift_restrictions and not shift.user_can_order_amount(user, amount=1):
        raise OrderException("User can not order that many products in this shift")

    if not product.orderable:
        raise OrderException("Product is not orderable")

    # Check Product availability
    if not product.available:
        raise OrderException("This product is not available")

    # Check Product-Shift availability
    if shift.venue not in product.available_at.all():
        raise OrderException("This Product is not available in this Shift")

    # Check per-Product order maximum
    if not product.user_can_order_amount(user, shift, amount=1):
        raise OrderException("User can not order {} {} for this shift".format(product, 1))

    return Order.objects.create(
        product=product,
        shift=shift,
        type=Order.TYPE_ORDERED,
        user=user,
        user_association=user.association,
        paid=paid,
        ready=ready,
        picked_up=picked_up,
        priority=priority,
    )


def add_user_to_assignees_of_shift(user, shift: Shift):
    """Add a user to the list of assignees for the shift."""
    if user in shift.assignees.all():
        return
    if not user_can_manage_shifts_in_venue(user, shift.venue):
        raise PermissionError("User does not have permissions to manage shifts in this venue.")
    shift.assignees.add(User.objects.get(pk=user.pk))
    shift.save()


def generate_order_statistics():
    """Generate statistics about orders per product."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - datetime.timedelta(days=365)

    for product in Product.objects.annotate(order_count=Count("orders", filter=Q(orders__created__gte=last_year))):
        data["labels"].append(str(product))
        data["datasets"][0]["data"].append(product.order_count)

    return data


def generate_orders_per_venue_statistics():
    """Generate statistics about orders per venue."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - datetime.timedelta(days=365)

    for venue in OrderVenue.objects.annotate(
        order_count=Count("shifts__orders", filter=Q(shifts__orders__created__gte=last_year))
    ):
        data["labels"].append(str(venue))
        data["datasets"][0]["data"].append(venue.order_count)

    return data
