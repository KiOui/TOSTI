from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Shift
from tantalus.models import TantalusShiftSynchronization
from tantalus.services import synchronize_to_tantalus


@receiver(post_save, sender=Shift)
def sync_to_tantalus(sender, instance, **kwargs):
    """Synchronize Orders to Tantalus if a Shift is made finalized."""
    if instance.finalized and not TantalusShiftSynchronization.objects.get(shift=instance).exists():
        if synchronize_to_tantalus(instance):
            TantalusShiftSynchronization.objects.create(shift=instance)
