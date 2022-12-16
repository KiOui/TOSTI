from constance import config
from django.contrib.sites.models import Site
from django.template.loader import get_template

from tosti.services import send_email
from venues import models


def send_reservation_request_email(reservation: models.Reservation):
    """Construct and send a reservation request email."""
    template = get_template("email/reservation.html")

    context = {
        "reservation": reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)

    recipients = config.VENUES_SEND_RESERVATION_REQUEST_EMAILS_TO.strip().split(",")

    return send_email("TOSTI: Reservation request", html_content, recipients)


def send_reservation_status_change_email(reservation: models.Reservation):
    """Construct and send a reservation status change email."""
    template = get_template("email/reservation_status.html")

    context = {
        "reservation": reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)

    return send_email("TOSTI: Reservation status change", html_content, [reservation.user.email])
