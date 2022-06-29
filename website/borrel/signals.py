from django.db.models.signals import pre_save
from django.dispatch import receiver

from borrel.models import BorrelReservation
from borrel.services import send_borrel_reservation_status_change_email


@receiver(pre_save, sender=BorrelReservation)
def send_borrel_reservation_status_change_email_receiver(sender, instance, **kwargs):
    """Send a status change email when the status of a BorrelReservation has been changed."""
    if instance.pk is not None:
        # Instance was updated
        old_instance = BorrelReservation.objects.get(pk=instance.pk)
        if old_instance.accepted != instance.accepted:
            send_borrel_reservation_status_change_email(instance)
