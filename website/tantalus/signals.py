from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Shift
from tantalus.models import TantalusShiftSynchronization
from tantalus.services import synchronize_shift_to_tantalus, TantalusClient


@receiver(post_save, sender=Shift)
def sync_shift_to_tantalus(sender, instance, **kwargs):
    """Synchronize Orders to Tantalus if a Shift is made finalized."""
    if (
        instance.finalized
        and TantalusClient.can_create_client()
        and not TantalusShiftSynchronization.objects.filter(shift=instance).exists()
    ):
        if synchronize_shift_to_tantalus(instance):
            TantalusShiftSynchronization.objects.create(shift=instance)
