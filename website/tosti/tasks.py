import logging
from smtplib import SMTPException


from celery import shared_task
import html2text
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from tosti.metrics import emit as emit_metric
from tosti.services import data_minimisation

logger = logging.getLogger(__name__)


@shared_task
def tosti_data_minimisation():
    """Minimise data in the database."""
    counts = data_minimisation(dry_run=False)
    emit_metric(
        "cron_data_minimisation_run",
        orders_affected=counts["orders"],
        thaliedje_affected=counts["thaliedje"],
        users_affected=counts["users"],
    )


@shared_task
def send_email(email_title: str, html_content: str, to: list[str], text_content=None):
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
