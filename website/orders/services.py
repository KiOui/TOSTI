import json
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
    # TODO: It could be that an Order exceeds Order limits after the dry run
    products_ignore_shift_restrictions = [x for x in products if x.ignore_shift_restrictions]

    if not shift.user_can_order_amount(user, amount=len(products) - len(products_ignore_shift_restrictions)):
        raise OrderException("User can not order that much products in this shift")

    for product in products:
        try:
            add_order(product, shift, Order.TYPE_ORDERED, user=user, dry=True)
        except OrderException as e:
            raise e

    for product in products:
        add_order(product, shift, Order.TYPE_ORDERED, user=user)


def add_order(product, shift, order_type, user=None, paid=False, ready=False, force=False, dry=False):
    """
    Add an order to a shift.

    :param product: the product for the order
    :param shift: the shift to add the order to
    :param order_type: the order type, if this is TYPE_ORDERED a user is needed
    :param user: the user to add the order to, can be None if the type is not TYPE_ORDERED
    :param paid: set paid for the new order
    :param ready: set ready for the new order
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
            raise OrderException("This shift is closed.")
        if not shift.is_active:
            raise OrderException("This shift is not active")

    if not dry:
        return Order.objects.create(
            product=product,
            shift=shift,
            type=order_type,
            user=user,
            user_association=user.profile.association if user is not None else None,
            paid=paid,
            ready=ready,
            order_price=product.current_price,
        )


def has_already_ordered_in_shift(user: User, shift: Shift):
    """Check if a user has already ordered in a shift."""
    return Order.objects.filter(user=user, shift=shift).exists()


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


class Cart:
    """Cart model for Orders."""

    def __init__(self, cart_items: List[Product]):
        """
        Initialize a Cart.

        :param cart_items: a List of Products indicating the Products in a Cart
        """
        self.cart_items = cart_items

    def get_item_list(self):
        """Get the item list."""
        return self.cart_items

    def get_item_list_ids(self):
        """Get the ids of all Products in the item list."""
        return [x.id for x in self.cart_items]

    @staticmethod
    def from_json(json_str):
        """
        Convert a JSON string to a Cart object.

        :param json_str: the JSON string
        :return: a Cart object or a JSONDecodeError on failed decoding
        """
        try:
            cart_item_ids = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise e

        return Cart.from_list(cart_item_ids)

    @staticmethod
    def from_list(cart_item_ids):
        """
        Convert a List of Product ids to a Cart.

        :param cart_item_ids: a List of Product ids
        :return: a Cart object or a ValueError if a Product could not be found
        """
        cart_items = list()
        for item_id in cart_item_ids:
            try:
                item = Product.objects.get(id=item_id)
                cart_items.append(item)
            except Product.DoesNotExist:
                raise ValueError(f"Product with id {item_id} does not exist.")

        return Cart(cart_items)

    def to_json(self):
        """Convert this object to JSON."""
        return json.dumps(self.get_item_list_ids())
