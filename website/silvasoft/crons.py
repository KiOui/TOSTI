from constance import config
from cron.core import CronJobBase, Schedule

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


class SynchronizeSilvasoft(CronJobBase):
    """Synchronize Borrel forms and Shifts to Silvasoft."""

    RUN_EVERY_MINS = 60
    RETRY_AFTER_FAILURE_MINS = 30
    code = "silvasoft.synchronize"
    schedule = Schedule(
        run_every_mins=RUN_EVERY_MINS, retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS
    )

    def do(self):
        """Synchronize Shifts and Borrel Reservations to Silvasoft."""
        if not SilvasoftClient.can_create_client():
            emit_metric("cron_silvasoft_sync_run", skipped_reason="no_client")
            return

        maximum_synchronizations_to_run = config.MAXIMUM_SYNC_PER_RUN
        succeeded = 0
        failed = 0

        borrel_reservations_to_synchronize = BorrelReservation.objects.filter(
            silvasoft_synchronization__isnull=True,
            submitted_at__isnull=False,
        ).order_by("submitted_at")

        for borrel_reservation in borrel_reservations_to_synchronize:
            if maximum_synchronizations_to_run == 0:
                emit_metric(
                    "cron_silvasoft_sync_run",
                    succeeded=succeeded,
                    failed=failed,
                    hit_limit=True,
                )
                return

            silvasoft_invoice, _ = (
                SilvasoftBorrelReservationInvoice.objects.get_or_create(
                    borrel_reservation=borrel_reservation
                )
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
                succeeded += 1
            except SilvasoftException:
                SilvasoftBorrelReservationSynchronization.objects.create(
                    borrel_reservation=borrel_reservation, succeeded=False
                )
                emit_metric(
                    "silvasoft_sync_failed",
                    kind="borrel_reservation",
                    reservation_id=borrel_reservation.pk,
                )
                failed += 1

            maximum_synchronizations_to_run = maximum_synchronizations_to_run - 1

        shifts_to_synchronize = Shift.objects.filter(
            silvasoft_synchronization__isnull=True,
            finalized=True,
        ).order_by("start")

        for shift in shifts_to_synchronize:
            if maximum_synchronizations_to_run == 0:
                emit_metric(
                    "cron_silvasoft_sync_run",
                    succeeded=succeeded,
                    failed=failed,
                    hit_limit=True,
                )
                return

            silvasoft_invoice, _ = SilvasoftShiftInvoice.objects.get_or_create(
                shift=shift
            )
            try:
                synchronize_shift_to_silvasoft(
                    shift, silvasoft_invoice.silvasoft_identifier
                )
                SilvasoftShiftSynchronization.objects.create(
                    shift=shift, succeeded=True
                )
                emit_metric(
                    "silvasoft_sync_succeeded",
                    kind="shift",
                    shift_id=shift.pk,
                )
                succeeded += 1
            except SilvasoftException:
                SilvasoftShiftSynchronization.objects.create(
                    shift=shift, succeeded=False
                )
                emit_metric(
                    "silvasoft_sync_failed",
                    kind="shift",
                    shift_id=shift.pk,
                )
                failed += 1

            maximum_synchronizations_to_run = maximum_synchronizations_to_run - 1

        emit_metric(
            "cron_silvasoft_sync_run",
            succeeded=succeeded,
            failed=failed,
            hit_limit=False,
        )
