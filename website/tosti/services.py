import calendar
import logging
from datetime import timedelta
from smtplib import SMTPException

import html2text
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from associations.models import Association
from borrel.models import ReservationItem
from orders.models import Product as OrderProduct, OrderVenue
from thaliedje.models import SpotifyTrack

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


def generate_order_statistics():
    """Generate statistics about orders per product."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for product in OrderProduct.objects.annotate(
        order_count=Count("orders", filter=Q(orders__created__gte=last_year))
    ):
        data["labels"].append(str(product))
        data["datasets"][0]["data"].append(product.order_count)

    return data


def generate_orders_per_venue_statistics():
    """Generate statistics about orders per venue."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for venue in OrderVenue.objects.annotate(
        order_count=Count("shifts__orders", filter=Q(shifts__orders__created__gte=last_year))
    ):
        data["labels"].append(str(venue))
        data["datasets"][0]["data"].append(venue.order_count)

    return data


def generate_most_requested_songs():
    """Generate statistics about the most requested songs."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for song in SpotifyTrack.objects.annotate(
        requested_amount=Count("requests", filter=Q(requests__added__gte=last_year))
    ).order_by("-requested_amount")[:10]:
        data["labels"].append(str(song.track_name))
        data["datasets"][0]["data"].append(song.requested_amount)

    return data


def generate_users_with_most_song_requests():
    """Generate statistics about users with the most song requests."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    last_year = timezone.now() - timedelta(days=365)

    for user in User.objects.annotate(
        requested_amount=Count("requests", filter=Q(requests__added__gte=last_year))
    ).order_by("-requested_amount")[:10]:
        data["labels"].append(str(user))
        data["datasets"][0]["data"].append(user.requested_amount)

    return data


def generate_users_per_association():
    """Generate statistics about users per association."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    for association in Association.objects.annotate(user_amount=Count("users")):
        data["labels"].append(str(association))
        data["datasets"][0]["data"].append(association.user_amount)

    return data


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
