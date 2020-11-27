import logging

import datetime
from typing import List

from django.utils import timezone

from orders.exceptions import OrderException
from orders.models import Order, Product, Shift
from users.models import User


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
            users.append(order.user)
            order.user = None
            if not dry_run:
                order.save()
        else:
            logging.warning(f"An unpaid order of {order.user} has not been touched.")
    return users


def user_can_order_product(user: User, product: Product, shift: Shift):
    """Check if a user can order products in a certain shift."""
    if user not in shift.venue.get_users_with_order_perms():
        raise OrderException("User does not have permissions to order during this shift.")
    if not shift.user_can_order_amount(user) and not product.ignore_shift_restrictions:
        raise OrderException("User can not order more products")
    if not product.user_can_order_amount(user, shift):
        raise OrderException(f"User can not order more {product.name}")
    return True


def place_orders(products: List[Product], user: User, shift: Shift):
    """Place orders for a user in a certain shift."""
    products_ignore_shift_restrictions = [x for x in products if x.ignore_shift_restrictions]

    if not shift.user_can_order_amount(user, amount=len(products) - len(products_ignore_shift_restrictions)):
        raise OrderException("User can not order that much products in this shift")

    orders = []
    for product in products:
        try:
            order = add_order(product, shift, Order.TYPE_ORDERED, user=user)
            orders.append(order)
        except OrderException as e:
            orders.append(e)

    return orders


def add_order(product, shift, order_type, user=None, set_done=False, force=False, dry=False):
    """
    Add an order to a shift.

    :param product: the product for the order
    :param shift: the shift to add the order to
    :param order_type: the order type, if this is TYPE_ORDERED a user is needed
    :param user: the user to add the order to, can be None if the type is not TYPE_ORDERED
    :param set_done: set paid and ready to done for the new order
    :param force: skip all checks and force add an order
    :param dry: do all checks but don't actually add the order
    :return: Either None if dry=True, an OrderException if the Order can't be added or a new Order object
    """
    if not force:
        # Product checks
        if not product.available:
            raise OrderException(f"Product {product.name} is not available")
        # Type checks
        if order_type is Order.TYPE_ORDERED and user is None:
            raise OrderException("A user is needed for items that have the 'TYPE_ORDERED' type.")
        # User limit checks
        if user is not None and user_can_order_product(user, product, shift):
            pass
        # Shift checks
        if not shift.can_order:
            raise OrderException("User can not order products for this shift")
        if not shift.is_active:
            raise OrderException("This shift is not active")

    if not dry:
        return Order.objects.create(
            product=product,
            shift=shift,
            type=order_type,
            user=user,
            user_association=user.profile.association,
            paid=set_done,
            ready=set_done,
            order_price=product.current_price,
        )


def has_already_ordered_in_shift(user: User, shift: Shift):
    """Check if a user has already ordered in a shift."""
    return Order.objects.filter(user=user, shift=shift).count() > 0


def add_user_to_assignees_of_shift(user, shift: Shift):
    """Add a user to the list of assignees for the shift."""
    if user not in shift.assignees.all():
        if user not in shift.venue.get_users_with_shift_admin_perms():
            raise OrderException("User does not have permissions to manage shifts in this venue.")
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
    """Extend the end_date of a shift."""
    shift.end_date += datetime.timedelta(minutes=amount_minutes)
    shift.save()
    return shift


def query_product_name(query):
    """Query a product name."""
    return Product.objects.filter(name__icontains=query, available=True)


def query_product_barcode(query):
    """Query a product barcode."""
    return Product.objects.filter(barcode__startswith=query, available=True)
