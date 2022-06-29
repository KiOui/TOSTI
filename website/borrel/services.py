import logging
from smtplib import SMTPException

from constance import config
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings

from borrel import models


logger = logging.getLogger(__name__)


def send_borrel_reservation_request_email(borrel_reservation: models.BorrelReservation):
    """Construct and send a borrel reservation email."""
    template = get_template("email/borrel_reservation.html")
    template_text = get_template("email/borrel_reservation.txt")

    context = {
        "borrel_reservation": borrel_reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)
    text_content = template_text.render(context)

    msg = EmailMultiAlternatives(
        "TOSTI: Borrel Reservation request",
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


def send_borrel_reservation_status_change_email(borrel_reservation: models.BorrelReservation):
    """Construct and send a borrel reservation status change email."""
    template = get_template("email/borrel_reservation_status.html")
    template_text = get_template("email/borrel_reservation_status.txt")

    context = {
        "borrel_reservation": borrel_reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)
    text_content = template_text.render(context)

    msg = EmailMultiAlternatives(
        "TOSTI: Borrel Reservation status change",
        text_content,
        settings.EMAIL_HOST_USER,
        [borrel_reservation.user_created.email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        return msg.send()
    except SMTPException as e:
        logger.error(e)
        return False
