import requests
from django.conf import settings

from tantalus.models import TantalusProduct


class TantalusException(Exception):
    """Tantalus Exception."""

    pass


class TantalusClient:
    """Tantalus Client."""

    def __init__(self, endpoint_url, username, password):
        """Initialise Tantalus Client by creating a session."""
        self.endpoint_url = endpoint_url
        session = requests.session()

        r = session.post(self.login_url, json={"username": username, "password": password})
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise TantalusException(e)

        self._session = session

    def get_products(self):
        """Get all registered Tantalus products."""
        r = self._session.get(self.products_url)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise TantalusException(e)
        return [{"name": x["name"], "id": x["id"]} for x in r.json()["products"]]

    def get_endpoints(self):
        """Get all registered Tantalus endpoints."""
        r = self._session.get(self.endpoints_url)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise TantalusException(e)
        return [{"name": x["name"], "id": x["id"]} for x in r.json()["endpoints"]]

    def register_order(self, product: TantalusProduct, amount: int, endpoint_id: int):
        """Register order in Tantalus."""
        try:
            r = self._session.post(
                self.sell_url, json={"product": product.tantalus_id, "endpoint": endpoint_id, "amount": amount}
            )
            r.raise_for_status()
        except requests.HTTPError as e:
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
    return TantalusClient(settings.TANTALUS_ENDPOINT_URL, settings.TANTALUS_USERNAME, settings.TANTALUS_PASSWORD,)


def sort_orders_by_product(orders):
    """Sort Orders by their Products."""
    sorted_orders = {}
    for order in orders:
        if order.product in sorted_orders.keys():
            sorted_orders[order.product].append(order)
        else:
            sorted_orders[order.product] = [order]
    return sorted_orders
