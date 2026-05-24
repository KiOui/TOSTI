from datetime import datetime

from constance import config
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.template.loader import get_template

from tosti.tasks import send_email
from venues import models


def create_reservation(
    *,
    venue: models.Venue,
    user,
    title: str,
    start: datetime,
    end: datetime,
    comments: str = "",
) -> models.Reservation:
    """Create an unaccepted reservation for ``venue`` on the user's behalf.

    Raises :class:`django.core.exceptions.ValidationError` if the venue
    doesn't accept reservations, the time window is invalid, or model-level
    validation fails. Sends the same notification email as the regular form
    flow on success.
    """
    if not venue.can_be_reserved:
        raise ValidationError(f"Venue '{venue}' does not accept reservations.")
    if end <= start:
        raise ValidationError("end must be after start.")

    reservation = models.Reservation(
        venue=venue,
        user_created=user,
        title=title,
        start=start,
        end=end,
        comments=comments,
    )
    reservation.full_clean()
    reservation.save()
    send_reservation_request_email(reservation)
    return reservation


def send_reservation_request_email(reservation: models.Reservation):
    """Construct and send a reservation request email."""
    template = get_template("email/reservation.html")

    context = {
        "reservation": reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)

    recipients = config.VENUES_SEND_RESERVATION_REQUEST_EMAILS_TO.strip().split(",")

    return send_email.delay("TOSTI: Reservation request", html_content, recipients)


def send_reservation_status_change_email(reservation: models.Reservation):
    """Construct and send a reservation status change email."""
    template = get_template("email/reservation_status.html")

    context = {
        "reservation": reservation,
        "domain": Site.objects.get_current().domain,
    }

    html_content = template.render(context)

    return send_email.delay(
        "TOSTI: Reservation status change",
        html_content,
        [user.email for user in reservation.users_access.all()],
    )
