from datetime import datetime

from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save)
def set_order_delivered_at_if_delivered(sender, instance, **kwargs):
    """Save when a order was delivered when it is set to delivered."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if instance.delivered and not obj.delivered:
            instance.delivered_at = datetime.now()
        if not instance.delivered and obj.delivered:
            instance.delivered_at = None


@receiver(pre_save)
def set_order_paid_at_if_paid(sender, instance, **kwargs):
    """Save when a order was delivered when it is set to delivered."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if instance.paid and not obj.paid:
            instance.paid_at = datetime.now()
        if not instance.paid and obj.paid:
            instance.paid_at = None
