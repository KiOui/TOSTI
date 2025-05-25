import logging
from smtplib import SMTPException

import html2text
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

import thaliedje.services
import orders.services
import users.services

logger = logging.getLogger(__name__)


User = get_user_model()


def send_email(email_title: str, html_content: str, to: list, text_content=None):
    """Send an email."""
    if text_content is None:
        h = html2text.HTML2Text()
        text_content = h.handle(html_content)

    msg = EmailMultiAlternatives(
        email_title,
        text_content,
        settings.EMAIL_HOST_USER,
        to,
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        return msg.send()
    except SMTPException as e:
        logger.error(e)
        return False


def data_minimisation(dry_run=False):
    """
    Execute data minimisation according to privacy policy.

    :param dry_run: does not really remove data if True
    :return: list of users from who data is removed
    """
    # This function should be implemented in the respective services.
    # For now, we just log the action.
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
    return []
