import requests
import logging
from settings.settings import settings

from orders.models import Shift, Order
from tantalus.models import TantalusProduct, TantalusOrderVenue


class TantalusException(Exception):
    """Tantalus Exception."""

    pass


class TantalusClient:
    """Tantalus Client."""

    def __init__(self, endpoint_url, username, password):
        """Initialise Tantalus Client by creating a session."""
        self.endpoint_url = endpoint_url
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
            settings.get_setting("tantalus_endpoint_url")
            and settings.get_setting("tantalus_username")
            and settings.get_setting("tantalus_password")
        )

    def get_products(self):
        """Get all registered Tantalus products."""
        try:
            r = self._session.get(self.products_url)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)
        return [{"name": x["name"], "id": x["id"]} for x in r.json()["products"]]

    def get_endpoints(self):
        """Get all registered Tantalus endpoints."""
        try:
            r = self._session.get(self.endpoints_url)
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(e)
        return [{"name": x["name"], "id": x["id"]} for x in r.json()["endpoints"]]

    def register_order(self, product: TantalusProduct, amount: int, endpoint_id: int):
        """Register order in Tantalus."""
        try:
            r = self._session.post(
                self.sell_url, json={"product": product.tantalus_id, "endpoint": endpoint_id, "amount": amount}
            )
            r.raise_for_status()
        except (requests.HTTPError, requests.ConnectionError) as e:
            raise TantalusException(
                "The following error occurred while registering TantalusProduct {} with amount {}: {}".format(
                    product, amount, e
                )
            )

    def get_full_url(self, path):
        """Get full URL."""
        return "{}{}".format(self.endpoint_url, path)

    @property
    def login_url(self):
        """Get login URL."""
        return self.get_full_url("login")

    @property
    def products_url(self):
        """Get products URL."""
        return self.get_full_url("products")

    @property
    def endpoints_url(self):
        """Get endpoints URL."""
        return self.get_full_url("endpoints")

    @property
    def sell_url(self):
        """Get sell URL."""
        return self.get_full_url("sell")


def get_tantalus_client() -> TantalusClient:
    """Get the default Tantalus client (with the login credentials in the Django settings file)."""
    return TantalusClient(
        settings.get_setting("tantalus_endpoint_url"),
        settings.get_setting("tantalus_username"),
        settings.get_setting("tantalus_password"),
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


def synchronize_to_tantalus(shift: Shift):
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
        logging.warning(
            "No Tantalus endpoint for {} exists, if you want to automatically synchronize to Tantalus,"
            " please add a TantalusOrderVenue for it.".format(shift.venue)
        )
        return False

    try:
        tantalus_client = get_tantalus_client()
    except TantalusException as e:
        logging.error(
            "Synchronization for Shift {} failed due to an Exception while initializing the Tantalus Client. The "
            "following Exception occurred: {}".format(shift, e)
        )
        return False

    orders = Order.objects.filter(shift=shift)
    for product, order_list in sort_orders_by_product(orders).items():
        try:
            tantalus_product = TantalusProduct.objects.get(product=product)
            tantalus_client.register_order(tantalus_product, len(order_list), venue.endpoint_id)
        except TantalusProduct.DoesNotExist:
            logging.warning(
                "Skipping Tantalus synchronization for Shift {} and Product {} as the Product is not connected"
                "to any TantalusProduct.".format(shift, product)
            )
        except TantalusException as e:
            logging.error(
                "Synchronization for Shift {} and Product {} failed with the following Exception: {}".format(
                    shift, product, e
                )
            )
    return True
