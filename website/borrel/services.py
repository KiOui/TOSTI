import logging

from constance import config
from django.contrib.sites.models import Site
from django.template.loader import get_template

from borrel import models
from tosti.services import send_email

logger = logging.getLogger(__name__)


def send_borrel_reservation_request_email(borrel_reservation: models.BorrelReservation):
    """Construct and send a borrel reservation email."""
    template = get_template("email/borrel_reservation.html")

    context = {
        "borrel_reservation": borrel_reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)

    return send_email(
        "TOSTI: Borrel Reservation request", html_content, [config.BORREL_SEND_BORREL_RESERVATION_REQUEST_EMAILS_TO]
    )


def send_borrel_reservation_status_change_email(borrel_reservation: models.BorrelReservation):
    """Construct and send a borrel reservation status change email."""
    template = get_template("email/borrel_reservation_status.html")

    context = {
        "borrel_reservation": borrel_reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)

    return send_email("TOSTI: Borrel Reservation status change", html_content, [borrel_reservation.user_created.email])
