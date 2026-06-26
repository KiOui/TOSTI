from django.contrib.auth import get_user_model
import logging

import thaliedje.services
import orders.services
import users.services

User = get_user_model()

logger = logging.getLogger(__name__)


def data_minimisation(dry_run=False):
    """
    Execute data minimisation according to privacy policy.

    :param dry_run: does not really remove data if True
    :return: dict with counts of records affected per category
    """
    logger.info("Executing data minimisation with dry_run={}".format(dry_run))
    processed_orders = orders.services.execute_data_minimisation(dry_run)
    for p in processed_orders:
        logger.info("Removed order data for {}".format(p))
    processed_thaliedje = thaliedje.services.execute_data_minimisation(dry_run)
    for p in processed_thaliedje:
        logger.info("Removed thaliedje data for {}".format(p))
    processed_users = users.services.execute_data_minimisation(dry_run)
    for p in processed_users:
        logger.info("Removed user account for {}".format(p))
    return {
        "orders": len(processed_orders),
        "thaliedje": len(processed_thaliedje),
        "users": len(processed_users),
    }
