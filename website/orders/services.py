import logging

from datetime import timedelta

from django.utils import timezone

from orders.models import Order


def execute_data_minimisation(dry_run=False):
    """
    Remove order history from users that is more than 31 days old

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