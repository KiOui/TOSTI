import logging

from borrel.models import BorrelReservation
from orders.models import Shift, Order

logger = logging.getLogger(__name__)


class SilvasoftException(Exception):
    """Silvasoft Exception."""

    pass


class SilvasoftClient:
    """Silvasoft Client."""

    @staticmethod
    def can_create_client():
        return False


def get_silvasoft_client():
    """Get the default Silvasoft client (with the login credentials in the Django settings file)."""
    pass


def synchronize_shift_to_silvasoft(shift: Shift):
    """
    Synchronize all Orders of a Shift to a Silvasoft endpoint.

    When finished successfully, this method will create an instance of SilvasoftShiftSynchronization connected to the
    synchronized Shift
    :param shift: the Shift to synchronize all Orders of
    :type shift: Shift
    :return: True if synchronization succeeded
    """
    pass


def synchronize_borrelreservation_to_silvasoft(borrel_reservation: BorrelReservation):
    """Synchronize a Borrel Reservation to Silvasoft."""
    pass
