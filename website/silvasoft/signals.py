from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Shift
from silvasoft.models import SilvasoftShiftSynchronization
from silvasoft.services import synchronize_shift_to_silvasoft, SilvasoftClient


@receiver(post_save, sender=Shift)
def sync_shift_to_silvasoft(sender, instance, **kwargs):
    """Synchronize Orders to Silvasoft if a Shift is made finalized."""
    if (
        instance.finalized
        and SilvasoftClient.can_create_client()
        and not SilvasoftShiftSynchronization.objects.filter(shift=instance).exists()
    ):
        if synchronize_shift_to_silvasoft(instance):
            SilvasoftShiftSynchronization.objects.create(shift=instance)
