import logging
from smtplib import SMTPException

import html2text
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

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
