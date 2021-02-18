import requests
from django.conf import settings

from tantalus.models import TantalusProduct


class TantalusException(Exception):
    """Tantalus Exception."""

    pass


class TantalusClient:
    """Tantalus Client."""

    def __init__(self, endpoint_url, username, password, endpoint_id):
        """Initialise Tantalus Client by creating a session."""
        self.endpoint_url = endpoint_url
        self.endpoint_id = endpoint_id
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

    def register_order(self, product: TantalusProduct, amount: int):
        """Register order in Tantalus."""
        try:
            r = self._session.post(
                self.sell_url, json={"product": product.tantalus_id, "endpoint": self.endpoint_id, "amount": amount}
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
    def sell_url(self):
        """Get sell URL."""
        return self.get_full_url("sell")


def get_tantalus_client() -> TantalusClient:
    """Get the default Tantalus client (with the login credentials in the Django settings file)."""
    return TantalusClient(
        settings.TANTALUS_ENDPOINT_URL,
        settings.TANTALUS_USERNAME,
        settings.TANTALUS_PASSWORD,
        settings.TANTALUS_ENDPOINT_ID,
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
