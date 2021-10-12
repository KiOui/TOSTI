from django.contrib.auth import get_user_model
from django.db.models import Q

from venues.models import Venue, Reservation

User = get_user_model()


def add_reservation(user: User, venue: Venue, start_time, end_time):
    """Add a reservation with a start and end time."""
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
    if user.profile.association is not None:
        return Reservation.objects.create(
            user=user, association=user.profile.association, venue=venue, start_time=start_time, end_time=end_time
        )
    else:
        return Reservation.objects.create(user=user, venue=venue, start_time=start_time, end_time=end_time)
