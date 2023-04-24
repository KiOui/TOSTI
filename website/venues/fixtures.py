from django.contrib.auth import get_user_model

from venues.models import Venue

User = get_user_model()


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
    pass