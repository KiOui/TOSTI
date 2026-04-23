from celery import shared_task
from constance import config

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


@shared_task
def synchronize_to_silvasoft():
    """Synchronize Shifts and Borrel Reservations to Silvasoft."""
    if not SilvasoftClient.can_create_client():
        return

    maximum_synchronizations_to_run = config.MAXIMUM_SYNC_PER_RUN

    borrel_reservations_to_synchronize = BorrelReservation.objects.filter(
        silvasoft_synchronization__isnull=True,
        submitted_at__isnull=False,
    ).order_by("submitted_at")

    for borrel_reservation in borrel_reservations_to_synchronize:
        if maximum_synchronizations_to_run == 0:
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
        except SilvasoftException:
            SilvasoftBorrelReservationSynchronization.objects.create(
                borrel_reservation=borrel_reservation, succeeded=False
            )

        maximum_synchronizations_to_run = maximum_synchronizations_to_run - 1

    shifts_to_synchronize = Shift.objects.filter(
        silvasoft_synchronization__isnull=True,
        finalized=True,
    ).order_by("start")

    for shift in shifts_to_synchronize:
        if maximum_synchronizations_to_run == 0:
            return

        silvasoft_invoice, _ = SilvasoftShiftInvoice.objects.get_or_create(shift=shift)
        try:
            synchronize_shift_to_silvasoft(
                shift, silvasoft_invoice.silvasoft_identifier
            )
            SilvasoftShiftSynchronization.objects.create(shift=shift, succeeded=True)
        except SilvasoftException:
            SilvasoftShiftSynchronization.objects.create(shift=shift, succeeded=False)

        maximum_synchronizations_to_run = maximum_synchronizations_to_run - 1
