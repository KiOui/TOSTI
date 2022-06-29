from django.db.models.signals import pre_save
from django.dispatch import receiver
from venues.services import send_reservation_status_change_email

from venues.models import Reservation


@receiver(pre_save, sender=Reservation)
def send_reservation_status_change_email_receiver(sender, instance, **kwargs):
    """Send a status change email when the status of a Reservation has been changed."""
    if instance.pk is None or instance.user is None:
        return

    old_instance = Reservation.objects.get(pk=instance.pk)
    if old_instance.accepted != instance.accepted:
        send_reservation_status_change_email(instance)
