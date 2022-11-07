import datetime

import requests
import logging
from constance import config

from borrel.models import BorrelReservation
from orders.models import Shift, Order
from tantalus.models import TantalusOrdersProduct, TantalusOrderVenue, TantalusAssociation, TantalusBorrelProduct

logger = logging.getLogger(__name__)


class TantalusException(Exception):
    """Tantalus Exception."""

    pass


class TantalusClient:
    """Tantalus Client."""

    def __init__(self, endpoint_url, api_url, username, password):
        """Initialise Tantalus Client by creating a session."""
        self.endpoint_url = endpoint_url
        self.api_url = api_url
        session = requests.session()

        try:
            r = session.post(self.login_url, json={"username": username, "password": password})
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)

        self._session = session

    @staticmethod
    def can_create_client():
        """Check whether all settings are instantiated."""
        return (
            config.TANTALUS_ENDPOINT_URL
            and config.TANTALUS_API_URL
            and config.TANTALUS_USERNAME
            and config.TANTALUS_PASSWORD
        )

    def get_pos_products(self):
        """Get all registered POS Tantalus products."""
        try:
            r = self._session.get(self.pos_products_url)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)
        return [{"name": x["name"], "id": x["id"]} for x in r.json()["products"]]

    def get_pos_endpoints(self):
        """Get all registered POS Tantalus endpoints."""
        try:
            r = self._session.get(self.pos_endpoints_url)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)
        return [{"name": x["name"], "id": x["id"]} for x in r.json()["endpoints"]]

    def get_relations(self):
        """Get all registered Tantalus relations."""
        try:
            r = self._session.get(self.relations_url)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)
        return r.json()["data"]

    def get_products(self):
        """Get all registered Tantalus products."""
        try:
            r = self._session.get(self.products_url)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)
        return r.json()["data"]

    def register_order(self, product: TantalusOrdersProduct, amount: int, endpoint_id: int):
        """Register order in Tantalus."""
        try:
            r = self._session.post(
                self.pos_sell_url, json={"product": product.tantalus_id, "endpoint": endpoint_id, "amount": amount}
            )
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(
                "The following error occurred while registering TantalusProduct {} with amount {}: {}".format(
                    product, amount, e
                )
            )

    def register_transaction(
        self,
        relation: TantalusAssociation,
        delivery_date: datetime.date,
        description: str = "",
        buy: list = None,
        sell: list = None,
        service: list = None,
        two_to_one_has_btw: bool = False,
        two_to_one_btw_per_row: bool = False,
    ):
        """Register a transaction in Tantalus."""
        data = {
            "relation": relation.tantalus_id,
            "description": description,
            "buy": buy if buy is not None else [],
            "sell": sell if sell is not None else [],
            "service": service if service is not None else [],
            "two_to_one_has_btw": two_to_one_has_btw,
            "two_to_one_btw_per_row": two_to_one_btw_per_row,
            "deliverydate": delivery_date.strftime("%Y-%m-%d"),
        }

        try:
            r = self._session.post(self.transactions_url, json=data)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(
                "The following error occurred while pushing a transaction to Tantalus: {}".format(e)
            )

    def get_pos_url(self, path):
        """Get point of sale URL."""
        return "{}{}".format(self.endpoint_url, path)

    def get_api_url(self, path):
        """Get API URL."""
        return "{}{}".format(self.api_url, path)

    @property
    def login_url(self):
        """Get login URL."""
        return self.get_pos_url("login")

    @property
    def pos_products_url(self):
        """Get POS products URL."""
        return self.get_pos_url("products")

    @property
    def pos_endpoints_url(self):
        """Get POS endpoints URL."""
        return self.get_pos_url("endpoints")

    @property
    def relations_url(self):
        """Get relations URL."""
        return self.get_api_url("relation")

    @property
    def transactions_url(self):
        """Get transactions URL."""
        return self.get_api_url("transaction")

    @property
    def products_url(self):
        """Get products URL."""
        return self.get_api_url("product")

    @property
    def pos_sell_url(self):
        """Get POS sell URL."""
        return self.get_pos_url("sell")


def get_tantalus_client() -> TantalusClient:
    """Get the default Tantalus client (with the login credentials in the Django settings file)."""
    if TantalusClient.can_create_client():
        return TantalusClient(
            config.TANTALUS_ENDPOINT_URL, config.TANTALUS_API_URL, config.TANTALUS_USERNAME, config.TANTALUS_PASSWORD
        )
    else:
        raise TantalusException(
            "TantalusClient could not be created, please provide valid settings for Tantalus to function."
        )


def sort_orders_by_product(orders):
    """Sort Orders by their Products."""
    sorted_orders = {}
    for order in orders:
        if order.product in sorted_orders.keys():
            sorted_orders[order.product].append(order)
        else:
            sorted_orders[order.product] = [order]
    return sorted_orders


def synchronize_shift_to_tantalus(shift: Shift):
    """
    Synchronize all Orders of a Shift to a Tantalus endpoint.

    When finished successfully, this method will create an instance of TantalusShiftSynchronization connected to the
    synchronized Shift
    :param shift: the Shift to synchronize all Orders of
    :type shift: Shift
    :return: True if synchronization succeeded
    """
    try:
        venue = TantalusOrderVenue.objects.get(order_venue=shift.venue)
    except TantalusOrderVenue.DoesNotExist:
        logger.warning(
            "No Tantalus endpoint for {} exists, if you want to automatically synchronize to Tantalus,"
            " please add a TantalusOrderVenue for it.".format(shift.venue)
        )
        return False

    try:
        tantalus_client = get_tantalus_client()
    except TantalusException as e:
        logger.error(
            "Synchronization for Shift {} failed due to an Exception while initializing the Tantalus Client. The "
            "following Exception occurred: {}".format(shift, e)
        )
        return False

    orders = Order.objects.filter(shift=shift)
    for product, order_list in sort_orders_by_product(orders).items():
        try:
            tantalus_product = TantalusOrdersProduct.objects.get(product=product)
            tantalus_client.register_order(tantalus_product, len(order_list), venue.endpoint_id)
        except TantalusOrdersProduct.DoesNotExist:
            logger.warning(
                "Skipping Tantalus synchronization for Shift {} and Product {} as the Product is not connected"
                "to any TantalusProduct.".format(shift, product)
            )
        except TantalusException as e:
            logger.error(
                "Synchronization for Shift {} and Product {} failed with the following Exception: {}".format(
                    shift, product, e
                )
            )
    return True


def synchronize_borrelreservation_to_tantalus(borrel_reservation: BorrelReservation):
    """Synchronize a Borrel Reservation to Tantalus."""
    try:
        tantalus_client = get_tantalus_client()
    except TantalusException as e:
        raise TantalusException(
            "Synchronization for Borrel Reservation {} failed due to an Exception while initializing the Tantalus "
            "Client. The following Exception occurred: {}".format(borrel_reservation, e)
        )

    if borrel_reservation.association is None:
        raise TantalusException(
            "No Association set for Borrel Reservation. Please first add an Association before synchronizing to "
            "Tantalus."
        )

    try:
        tantalus_relation = TantalusAssociation.objects.get(association=borrel_reservation.association)
    except TantalusAssociation.DoesNotExist:
        raise TantalusException(
            "No Tantalus Association exists for {}, if you want to automatically synchronize to Tantalus,"
            " please add a Tantalus Association for it.".format(borrel_reservation.association)
        )

    reservation_items_to_submit = {}
    for reservation_item in borrel_reservation.items.filter(product__can_be_submitted=True):
        if reservation_item.amount_used is None:
            raise TantalusException(
                "The amount used for {} is not filled in yet, please register how much is used for {} and then rerun "
                "synchronization.".format(reservation_item.product, reservation_item.product)
            )

        if reservation_item.amount_used == 0:
            continue

        try:
            tantalus_borrel_product = TantalusBorrelProduct.objects.get(product=reservation_item.product)
        except TantalusBorrelProduct.DoesNotExist:
            raise TantalusException(
                "No Tantalus Borrel Product exists for {}, if you want to automatically synchronize to Tantalus,"
                " please add a Tantalus Borrel Product for it.".format(reservation_item.product)
            )

        reservation_items_to_submit[tantalus_borrel_product] = reservation_item.amount_used

    try:
        tantalus_client.register_transaction(
            tantalus_relation,
            borrel_reservation.start,
            description=borrel_reservation.title,
            sell=[
                {"id": tantalus_product.tantalus_id, "amount": amount}
                for tantalus_product, amount in reservation_items_to_submit.items()
            ],
        )
    except TantalusException as e:
        raise TantalusException(
            "The following exception occurred while synchronising {} to Tantalus: {}".format(borrel_reservation, e)
        )

    return True
