from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from venues.models import Venue, Reservation

User = get_user_model()


def add_reservation(user: User, venue: Venue, start, end, title):
    """Add a reservation with a start and end time."""
    if start < timezone.now():
        raise ValueError("Reservation start date should be in the future.")
    elif end <= start:
        raise ValueError("Reservation start date should be before end date.")
    elif (
        Reservation.objects.filter(venue=venue)
        .filter(
            Q(start__lte=start, end__gt=start) | Q(start__lt=end, end__gte=end) | Q(start__gte=start, end__lte=end)
        )
        .exists()
    ):
        raise ValueError("Can not create an overlapping reservation for the same venue.")

    return Reservation.objects.create(
        user=user,
        association=user.profile.association,
        venue=venue,
        start=start,
        end=end,
        title=title,
    )
