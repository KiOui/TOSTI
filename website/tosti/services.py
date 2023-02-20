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
from orders.models import Product as OrderProduct, OrderVenue
from borrel.models import Product as BorrelProduct
from thaliedje.models import SpotifyTrack
from constance import config

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


def generate_beer_ordered_per_association():
    """Generate statistics about beer ordered per association."""
    try:
        beer_product = BorrelProduct.objects.get(id=config.STATISTICS_BEER_ID)
    except BorrelProduct.DoesNotExist:
        return None

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
                borrel_reservations__items__product=beer_product,
            ),
        )
    ):
        data["labels"].append(str(association))
        data["datasets"][0]["data"].append(association.ordered_beer_amount)

    return data
