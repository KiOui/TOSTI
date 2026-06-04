from celery import shared_task

from borrel.models import BorrelReservation
from orders.models import Shift
from silvasoft.models import (
    SilvasoftShiftInvoice,
    SilvasoftShiftSynchronization,
    SilvasoftBorrelReservationSynchronization,
    SilvasoftBorrelReservationInvoice,
)
from silvasoft.services import (
    synchronize_shift_to_silvasoft,
    SilvasoftException,
    synchronize_borrelreservation_to_silvasoft,
    SilvasoftClient,
)
from tosti.metrics import emit as emit_metric


@shared_task
def task_synchronize_shift_to_silvasoft(shift_pk: int):
    """
    Celery task wrapper for synchronizing a Shift to Silvasoft.

    This tasks takes the ID of the object because the arguments need to be serializable.
    """
    try:
        shift = Shift.objects.get(pk=shift_pk)
    except Shift.DoesNotExist:
        emit_metric("cron_silvasoft_shift_sync_run", skipped_reason="id_does_not_exist")
        return

    if not SilvasoftClient.can_create_client():
        emit_metric("cron_silvasoft_shift_sync_run", skipped_reason="no_client")
        return

    silvasoft_invoice, _ = SilvasoftShiftInvoice.objects.get_or_create(shift=shift)
    try:
        synchronize_shift_to_silvasoft(shift, silvasoft_invoice.silvasoft_identifier)
        SilvasoftShiftSynchronization.objects.create(shift=shift, succeeded=True)
        emit_metric(
            "silvasoft_sync_succeeded",
            kind="shift",
            shift_id=shift.pk,
        )
    except SilvasoftException:
        SilvasoftShiftSynchronization.objects.create(shift=shift, succeeded=False)
        emit_metric(
            "silvasoft_sync_failed",
            kind="shift",
            shift_id=shift.pk,
        )


@shared_task
def task_synchronize_borrel_reservation_to_silvasoft(
    borrel_reservation_pk: int,
):
    """
    Celery task wrapper for synchronizing a Borrel Reservation to Silvasoft.

    This tasks takes the ID of the object because the arguments need to be serializable.
    """
    try:
        borrel_reservation = BorrelReservation.objects.get(pk=borrel_reservation_pk)
    except Shift.DoesNotExist:
        emit_metric("cron_silvasoft_shift_sync_run", skipped_reason="id_does_not_exist")
        return

    if not SilvasoftClient.can_create_client():
        emit_metric(
            "cron_silvasoft_borrel_reservation_sync_run", skipped_reason="no_client"
        )
        return

    silvasoft_invoice, _ = SilvasoftBorrelReservationInvoice.objects.get_or_create(
        borrel_reservation=borrel_reservation
    )
    try:
        synchronize_borrelreservation_to_silvasoft(
            borrel_reservation, silvasoft_invoice.silvasoft_identifier
        )
        SilvasoftBorrelReservationSynchronization.objects.create(
            borrel_reservation=borrel_reservation, succeeded=True
        )
        emit_metric(
            "silvasoft_sync_succeeded",
            kind="borrel_reservation",
            reservation_id=borrel_reservation.pk,
        )
    except SilvasoftException:
        SilvasoftBorrelReservationSynchronization.objects.create(
            borrel_reservation=borrel_reservation, succeeded=False
        )
        emit_metric(
            "silvasoft_sync_failed",
            kind="borrel_reservation",
            reservation_id=borrel_reservation.pk,
        )
