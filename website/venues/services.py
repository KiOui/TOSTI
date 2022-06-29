import logging
from smtplib import SMTPException

from constance import config
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings

from venues import models


logger = logging.getLogger(__name__)


def send_reservation_request_email(reservation: models.Reservation):
    """Construct and send a reservation request email."""
    template = get_template("email/reservation.html")
    template_text = get_template("email/reservation.txt")

    context = {
        "reservation": reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)
    text_content = template_text.render(context)

    msg = EmailMultiAlternatives(
        "TOSTI: Reservation request",
        text_content,
        settings.EMAIL_HOST_USER,
        [config.SEND_EMAIL_TO],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        return msg.send()
    except SMTPException as e:
        logger.error(e)
        return False


def send_reservation_status_change_email(reservation: models.Reservation):
    """Construct and send a reservation status change email."""
    template = get_template("email/reservation_status.html")
    template_text = get_template("email/reservation_status.txt")

    context = {
        "reservation": reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)
    text_content = template_text.render(context)

    msg = EmailMultiAlternatives(
        "TOSTI: Reservation status change",
        text_content,
        settings.EMAIL_HOST_USER,
        [reservation.user.email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        return msg.send()
    except SMTPException as e:
        logger.error(e)
        return False
