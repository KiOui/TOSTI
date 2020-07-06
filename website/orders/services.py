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
    delete_before = timezone.now() - timedelta(days=31)
    orders = Order.objects.filter(created__lte=delete_before)

    users = []
    for order in orders:
        if not order.paid:
            users.append(order.user)
            order.user = None
            if not dry_run:
                order.save()
        else:
            logging.warning(f"An unpaid order of {order.user.get_full_name()} has not been touched.")
    return users

def user_can_order_product(user: User, product: Product, shift: Shift):
    """Check if a user can order products in a certain shift."""
    if not shift.user_can_order_amount(user):
        raise OrderException("You can not order more products")
    if not product.user_can_order_amount(user, shift):
        raise OrderException(f"You can not order more {product.name}")
    if not product.available:
        raise OrderException(f"Product {product.name} is not available")
    return True

def place_orders(products: List[Product], user: User, shift: Shift):
    """Place orders for a user in a certain shift."""
    if not shift.user_can_order_amount(user, amount=len(products)):
        raise OrderException("You can't order that much products in this shift")
    if not shift.can_order:
        raise OrderException("You can not order products for this shift")
    if not shift.is_active:
        raise OrderException("This shift is not active")

    for product in products:
        if not user_can_order_product(user, product, shift):
            return

    orders = []
    for product in products:
        orders.append(Order.objects.create(
            user=user, shift=shift, product=product
        ))

    return orders

def has_already_ordered_in_shift(user: User, shift: Shift):
    """Check if a user has already ordered in a shift."""
    return Order.objects.filter(user=user, shift=shift).count() > 0

def add_user_to_assignees_of_shift(user: User, shift: Shift):
    """Add a user to the list of assignees for the shift."""
    assignees = shift.assignees.all()
    if user not in assignees:
        shift.assignees.add(user)
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
