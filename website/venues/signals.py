from django.db.models import Q
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from venues.services import send_reservation_status_change_email

from venues.models import Reservation


@receiver(pre_save, sender=Reservation)
def send_reservation_status_change_email_receiver(sender, instance, **kwargs):
    """Send a status change email when the status of a Reservation has been changed."""
    if instance.pk is None or instance.user_created is None:
        return

    try:
        old_instance = Reservation.objects.get(pk=instance.pk)
    except Reservation.DoesNotExist:
        return

    if old_instance.accepted != instance.accepted:
        send_reservation_status_change_email(instance)


@receiver(post_save, sender=Reservation)
def set_reservation_accepted_if_automatic_reservations_are_enabled(
    sender, instance, created, **kwargs
):
    """Set a reservation to accepted if enabled on the venue."""
    if not created:
        return

    if not instance.venue.automatically_accept_first_reservation:
        return

    if instance.accepted is not None:
        return

    if (
        Reservation.objects.filter(venue=instance.venue)
        .filter(
            Q(start__lte=instance.start, end__gt=instance.start)
            | Q(start__lt=instance.end, end__gte=instance.end)
            | Q(start__gte=instance.start, end__lte=instance.end)
        )
        .exclude(pk=instance.pk)
        .exclude(accepted=False)
        .exists()
    ):
        # If there is an overlapping reservation
        return

    instance.accepted = True
    instance.save()
