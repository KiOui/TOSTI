import datetime
import logging

from django.utils import timezone

from orders.exceptions import OrderException
from orders.models import Order, Product, Shift
from users.models import User


logger = logging.getLogger(__name__)


def execute_data_minimisation(dry_run=False):
    """
    Remove order history from users that is more than 31 days old.

    :param dry_run: does not really remove data if True
    :return: list of users from who data is removed
    """
    delete_before = timezone.now() - datetime.timedelta(days=31)
    orders = Order.objects.filter(created__lte=delete_before)

    users = []
    for order in orders:
        if not order.paid:
            logger.warning(f"An unpaid order of {order.user} has not been touched.")
        else:
            users.append(order.user)
            order.user = None
            if not dry_run:
                order.save()
    return users


def add_scanned_order(product: Product, shift: Shift, ready=True, paid=True) -> Order:
    """
    Add a single Scanned Order (of type TYPE_SCANNED).

    :param product: A Product for which an Order has to be created
    :param shift: The shift for which the Orders have to be created
    :param ready: Whether or not the Order should be directly made ready
    :param paid: Whether or not the Order should be directly made paid
    :return: The created Order
    """
    # Check if Shift is not finalized
    if shift.finalized:
        raise OrderException("Shift is finalized, no Orders can be added anymore")

    # Check if Shift is active
    if not shift.is_active:
        raise OrderException("Shift is not active")

    # Check Product availability
    if not product.available:
        raise OrderException("This Product is not available")

    # Check Product-Shift availability
    if shift.venue not in product.available_at.all():
        raise OrderException("This Product is not available in this Shift")

    return Order.objects.create(
        product=product, shift=shift, type=Order.TYPE_SCANNED, user=None, user_association=None, ready=ready, paid=paid
    )


def add_user_order(product: Product, shift: Shift, user: User) -> Order:
    """
    Add a single Order (of type TYPE_ORDERED).

    :param product: A Product for which an Order has to be created
    :param shift: The shift for which the Orders have to be created
    :param user: The User for which the Orders have to be created
    :return: The created Order
    """
    # Check order permissions
    if not user.has_perm("orders.can_order_in_venue", shift.venue):
        raise OrderException("User has no order permission for this Venue.")

    # Check if Shift is not finalized
    if shift.finalized:
        raise OrderException("Shift is finalized, no Orders can be added anymore")

    # Check if Shift is active
    if not shift.is_active:
        raise OrderException("Shift is not active")

    # Check if Shift is not closed
    if not shift.can_order:
        raise OrderException("This Shift is closed.")

    # Check Shift order maximum while ignoring Products without Shift restrictions
    if not product.ignore_shift_restrictions and not shift.user_can_order_amount(user, amount=1):
        raise OrderException("User can not order that many products in this shift")

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
        user_association=user.profile.association,
    )


def add_user_to_assignees_of_shift(user, shift: Shift):
    """Add a user to the list of assignees for the shift."""
    if user not in shift.assignees.all():
        if user not in shift.venue.get_users_with_shift_admin_perms():
            raise PermissionError("User does not have permissions to manage shifts in this venue.")
        shift.assignees.add(User.objects.get(pk=user.pk))
        shift.save()


def set_shift_active(shift, value):
    """Activate a shift for ordering."""
    shift.can_order = value
    shift.save()
    return shift


def set_order_ready(order, value):
    """Set a order's 'ready' value."""
    order.ready = value
    order.save()
    return order


def set_order_paid(order, value):
    """Set a order's 'paid' value."""
    order.paid = value
    order.save()
    return order


def increase_shift_capacity(shift, amount=5):
    """Increase the maximum amount of accepting orders for a shift."""
    shift.max_orders_total += amount
    shift.save()
    return shift


def increase_shift_time(shift, amount_minutes=5):
    """Extend the end of a shift."""
    shift.end += datetime.timedelta(minutes=amount_minutes)
    shift.save()
    return shift


def query_product_name(query):
    """Query a product name."""
    return Product.objects.filter(name__icontains=query, available=True)


def query_product_barcode(query):
    """Query a product barcode."""
    return Product.objects.filter(barcode__startswith=query, available=True)
