from datetime import datetime

import pytz
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings

from orders.models import Order


@receiver(pre_save, sender=Order)
def set_order_paid_at_if_paid(sender, instance, **kwargs):
    """Save when a order was paid when it is set to paid."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        if instance.paid:
            timezone = pytz.timezone(settings.TIME_ZONE)
            localized_now = timezone.localize(datetime.now())
            instance.paid_at = localized_now
    else:
        if instance.paid and not obj.paid:
            timezone = pytz.timezone(settings.TIME_ZONE)
            localized_now = timezone.localize(datetime.now())
            instance.paid_at = localized_now
        if not instance.paid and obj.paid:
            instance.paid_at = None


@receiver(pre_save, sender=Order)
def set_order_ready_at_if_ready(sender, instance, **kwargs):
    """Save when a order was ready when it is set to ready."""
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        if instance.ready:
            timezone = pytz.timezone(settings.TIME_ZONE)
            localized_now = timezone.localize(datetime.now())
            instance.ready_at = localized_now
    else:
        if instance.ready and not obj.ready:
            timezone = pytz.timezone(settings.TIME_ZONE)
            localized_time = timezone.localize(datetime.now())
            instance.ready_at = localized_time
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
