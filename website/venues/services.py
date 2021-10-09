import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q

from venues.models import Venue, Reservation

User = get_user_model()


def add_reservation(user: User, venue: Venue, start_time, end_time):
    """Add a reservation with a start and end time."""
    timezone = pytz.timezone(settings.TIME_ZONE)

    start_time = start_time.astimezone(timezone)
    end_time = end_time.astimezone(timezone)

    if (
        Reservation.objects.filter(venue=venue)
        .filter(
            Q(start_time__lte=start_time, end_time__gt=start_time)
            | Q(start_time__lt=end_time, end_time__gte=end_time)
            | Q(start_time__gte=start_time, end_time__lte=end_time)
        )
        .exists()
    ):
        raise ValueError("Can not create an overlapping reservation for the same venue.")

    return Reservation.objects.create(user=user, venue=venue, start_time=start_time, end_time=end_time)
