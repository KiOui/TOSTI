import calendar
from datetime import timedelta

from constance import config
from django.contrib.sites.models import Site
from django.db.models import Sum, Count, Q
from django.template.loader import get_template
from django.utils import timezone

from associations.models import Association
from borrel import models
from borrel.models import ReservationItem
from tosti.services import send_email


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


def generate_product_category_ordered_per_association(category):
    """Generate statistics about products in a category ordered per association."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for association in Association.objects.annotate(
        ordered_beer_amount=Sum(
            "borrel_reservations__items__amount_used",
            filter=Q(
                borrel_reservations__submitted_at__isnull=False,
                borrel_reservations__start__gte=last_year,
                borrel_reservations__items__product__category=category,
            ),
        )
    ):
        data["labels"].append(str(association))
        data["datasets"][0]["data"].append(association.ordered_beer_amount)

    return data


def generate_beer_per_association_per_borrel(category):
    """Generate statistics about products in a category ordered per association per borrel."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for association in Association.objects.annotate(
        ordered_beer_amount=Sum(
            "borrel_reservations__items__amount_used",
            filter=Q(
                borrel_reservations__submitted_at__isnull=False,
                borrel_reservations__start__gte=last_year,
                borrel_reservations__items__product__category=category,
            ),
        ),
        borrel_reservation_amount=Count(
            "borrel_reservations",
            filter=Q(
                borrel_reservations__submitted_at__isnull=False,
                borrel_reservations__start__gte=last_year,
            ),
            distinct=True,
        ),
    ):
        if association.ordered_beer_amount is None:
            association.ordered_beer_amount = 0
        data["labels"].append(str(association))
        data["datasets"][0]["data"].append(
            association.ordered_beer_amount / association.borrel_reservation_amount
            if association.borrel_reservation_amount != 0
            else 0
        )

    return data


def generate_beer_consumption_over_time(category):
    """Generate statistics about products in a category ordered per month."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    current_year = last_year.year
    current_month = last_year.month

    for i in range(0, 13):

        next_month = current_month + 1
        if next_month > 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_year = current_year

        begin_date = timezone.make_aware(timezone.datetime(year=current_year, month=current_month, day=1))
        end_date = timezone.make_aware(timezone.datetime(year=next_year, month=next_month, day=1))

        amount_of_beer_ordered = ReservationItem.objects.filter(
            reservation__end__gte=begin_date, reservation__end__lt=end_date, product__category=category
        ).aggregate(beer_used=Sum("amount_used"))
        data["labels"].append(str(calendar.month_name[current_month]))
        data["datasets"][0]["data"].append(
            amount_of_beer_ordered["beer_used"] if amount_of_beer_ordered["beer_used"] is not None else 0
        )

        current_month = current_month + 1
        if current_month > 12:
            current_month = 1
            current_year = current_year + 1

    return data
