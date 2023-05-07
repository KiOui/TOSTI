import math
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from venues.models import Venue, Reservation
from faker import Factory as FakerFactory

User = get_user_model()


faker = FakerFactory.create("nl_NL")


def generate_title():
    """Generate a random title."""
    words = faker.words(random.randint(1, 3))
    return " ".join([word.capitalize() for word in words])


def create_fixtures():
    """Create random fixtures."""
    create_venues()
    create_random_reservations()


def create_venues():
    """Create fixtures for OrderVenue's."""
    Venue.objects.create(
        name="Noordkantine",
        slug="noordkantine",
        active=True,
        color_in_calendar="#0d6efd",
        can_be_reserved=True,
        automatically_accept_first_reservation=False,
    )
    Venue.objects.create(
        name="Zuidkantine",
        slug="zuidkantine",
        active=True,
        color_in_calendar="#dc3545",
        can_be_reserved=True,
        automatically_accept_first_reservation=False,
    )


def create_random_reservations():
    """Create randomized reservations."""
    for i in range(0, 50):
        try:
            create_random_reservation()
        except ValidationError:
            pass


def create_random_reservation():
    """Create a random Reservation."""
    reservation = Reservation()
    reservation.comments = faker.paragraph()
    reservation.title = generate_title()
    reservation.start = faker.date_time_between("-30d", "+30d", timezone.get_current_timezone())
    duration_hour = math.ceil(random.expovariate(0.2))
    reservation.end = reservation.start + timedelta(hours=duration_hour)
    reservation.venue = Venue.objects.order_by("?").first()
    reservation.user_created = User.objects.order_by("?").first()
    users_that_have_access_count = math.ceil(random.expovariate(0.2)) - 1
    reservation.accepted = random.choice([True, True, True, False, None, None])
    reservation.clean()
    reservation.save()
    users_that_have_access = [x for x in User.objects.order_by("?")[:users_that_have_access_count]]

    for user in users_that_have_access:
        reservation.users_access.add(user)
