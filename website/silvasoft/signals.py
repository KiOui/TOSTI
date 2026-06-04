from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from borrel.models import BorrelReservation
from orders.models import Shift
from silvasoft.models import (
    SilvasoftBorrelReservationSynchronization,
    SilvasoftShiftSynchronization,
)
from silvasoft.tasks import (
    task_synchronize_borrel_reservation_to_silvasoft,
    task_synchronize_shift_to_silvasoft,
)


def cache_previous_object(sender, instance):
    """Cache the value of an object in the database in the `__object_pre_save` property."""
    original_object = None
    if instance.id:
        original_object = sender.objects.get(pk=instance.id)

    instance._object_pre_save = original_object


@receiver(pre_save, sender=BorrelReservation)
def cache_previous_borrel_reservation(
    sender, instance: BorrelReservation, *args, **kwargs
):
    """
    Cache the value of a `BorrelReservation` before an update occurs.

    We need to cache the `BorrelReservation` object before an update to the database because we need to see whether it
    was marked completed in the `post_save` signal.
    """
    cache_previous_object(sender, instance)


@receiver(pre_save, sender=Shift)
def cache_previous_shift(sender, instance: Shift, *args, **kwargs):
    """
    Cache the value of a `Shift` before an update occurs.

    We need to cache the `Shift` object before an update to the database because we need to see whether it was marked
    completed in the `post_save` signal.
    """
    cache_previous_object(sender, instance)


@receiver(post_save, sender=BorrelReservation)
def send_borrel_reservation_to_silvasoft_on_submission(
    sender, instance: BorrelReservation, created, **kwargs
):
    """Send a `BorrelReservation` object to Silvasoft when `submitted_at` is set."""
    if (
        hasattr(instance, "_object_pre_save")
        and instance._object_pre_save is not None
        and instance._object_pre_save.submitted_at is None
        and instance.submitted_at is not None
        and not SilvasoftBorrelReservationSynchronization.objects.filter(
            borrel_reservation=instance
        ).exists()
    ):
        # Instance was submitted
        task_synchronize_borrel_reservation_to_silvasoft(instance.pk).delay()


@receiver(post_save, sender=Shift)
def send_shift_to_silvasoft_on_finalization(sender, instance: Shift, created, **kwargs):
    """Send a `Shift` object to Silvasoft when the `Shift` is made finalized."""
    if (
        hasattr(instance, "_object_pre_save")
        and instance._object_pre_save is not None
        and instance._object_pre_save.finalized is False
        and instance.finalized is True
        and not SilvasoftShiftSynchronization.objects.filter(shift=instance).exists()
    ):
        # Instance was submitted
        task_synchronize_shift_to_silvasoft(instance.pk).delay()
