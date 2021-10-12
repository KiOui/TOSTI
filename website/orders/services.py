import datetime
import json
import logging
from collections import Counter
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


def add_user_orders(products: [Product], shift: Shift, user: User) -> [Order]:
    """
    Add a list of User orders after checking if those orders can be added.

    :param products: A list of Products for which Orders have to be created
    :param shift: The shift for which the Orders have to be created
    :param user: The User for which the Orders have to be created
    :return: A list of created Orders
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
    products_ignore_shift_restrictions = [x for x in products if x.ignore_shift_restrictions]
    if not shift.user_can_order_amount(user, amount=len(products) - len(products_ignore_shift_restrictions)):
        raise OrderException("User can not order that many products in this shift")

    mapped_product_amounts = Counter(products)
    for product, amount in mapped_product_amounts.items():
        # Check Product availability
        if not product.available:
            raise OrderException("This product is not available")

        # Check Product-Shift availability
        if shift.venue not in product.available_at.all():
            raise OrderException("This Product is not available in this Shift")

        # Check per-Product order maximum
        if not product.user_can_order_amount(user, shift, amount=amount):
            raise OrderException("User can not order {} {} for this shift".format(product, amount))

    return [
        Order.objects.create(
            product=product,
            shift=shift,
            type=Order.TYPE_ORDERED,
            user=user,
            user_association=user.profile.association,
        )
        for product in products
    ]


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
    if not shift.user_can_order_amount(user, amount=1):
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
