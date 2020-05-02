from datetime import datetime

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from orders.models import Order


@receiver(pre_save, sender=Order)
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


@receiver(pre_save, sender=Order)
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


@receiver(pre_save, sender=Order)
def set_order_ready_at_if_ready(sender, instance, **kwargs):
    """Save when a order was ready when it is set to ready."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if instance.ready and not obj.ready:
            instance.ready_at = datetime.now()
        if not instance.ready and obj.ready:
            instance.ready_at = None


@receiver(pre_save, sender=Order)
def copy_order_price(sender, instance, **kwargs):
    """Copy the product price to an order."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if not instance.product == obj.product:
            instance.order_price = instance.product.current_price


@receiver(post_save, sender=Order)
def update_shift_capacity_can_order(sender, instance, **kwargs):
    """Update the can_order field from a shift when an order is placed."""
    shift = instance.shift
    shift.update_can_order()
