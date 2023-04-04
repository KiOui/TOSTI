import logging
import urllib.parse

import requests
from constance import config

from borrel.models import BorrelReservation
from orders.models import Shift, Order
from silvasoft.models import CachedRelation, CachedProduct

logger = logging.getLogger(__name__)


class SilvasoftException(Exception):
    """Silvasoft Exception."""

    def __init__(self, response=None):
        self.response = response


class SilvasoftClient:
    """Silvasoft Client."""

    def __init__(self, endpoint_url, username, api_key):
        """Initialise Silvasoft Client by creating a session."""
        self.endpoint_url = endpoint_url
        self.username = username
        self.api_key = api_key

    @staticmethod
    def can_create_client():
        """Check whether all settings are instantiated."""
        return config.SILVASOFT_API_URL and config.SILVASOFT_USERNAME and config.SILVASOFT_API_KEY

    def get_api_url(self, path):
        """Get API URL."""
        return "{}{}".format(self.endpoint_url, path)

    def get_authentication_headers(self):
        return {"ApiKey": self.api_key, "Username": self.username}

    def get(self, path, **kwargs):
        """Send a GET request."""
        headers = self.get_authentication_headers()
        headers["Content-Type"] = "application/json"
        parameters = urllib.parse.urlencode(kwargs)
        path = "{}?{}".format(path, parameters)
        response = requests.get(path, headers=headers)
        if response.status_code != 200:
            raise SilvasoftException(response=response)
        else:
            return response.json()

    @staticmethod
    def get_all(func, max_per_iteration=50, *args, **kwargs):
        start = 0
        zero_results = False
        all_results = []
        function_kwargs = {
            "Sorting": "createdDate",
            "SortDir": "DEC",
        }
        function_kwargs.update(kwargs)
        while not zero_results:
            function_kwargs.update(Limit=max_per_iteration, Offset=start)
            results = func(*args, **function_kwargs)
            all_results = all_results + results
            start = start + max_per_iteration
            if len(results) != max_per_iteration:
                zero_results = True
        return all_results

    def post(self, path, **kwargs):
        """Send a POST request."""
        headers = self.get_authentication_headers()

    def list_relations(self, **kwargs):
        return self.get(self.list_relations_url, **kwargs)

    def list_products(self, **kwargs):
        return self.get(self.list_products_url, **kwargs)

    @property
    def list_relations_url(self):
        """Get list relations URL."""
        return self.get_api_url("listrelations/")

    @property
    def list_products_url(self):
        """Get list products URL."""
        return self.get_api_url("listproducts/")

    @property
    def add_order_url(self):
        """Add order URL."""
        return self.get_api_url("addorder/")

    @property
    def add_sales_transaction_url(self):
        """Add sales transaction URL."""
        return self.get_api_url("addsalestransaction/")


def get_silvasoft_client() -> SilvasoftClient:
    """Get the default Silvasoft client (with the login credentials in the Django settings file)."""
    if SilvasoftClient.can_create_client():
        return SilvasoftClient(config.SILVASOFT_API_URL, config.SILVASOFT_USERNAME, config.SILVASOFT_API_KEY)
    else:
        raise SilvasoftException(
            "SilvasoftClient could not be created, please provide valid settings for Silvasoft to function."
        )


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


def refresh_cached_relations():
    client = get_silvasoft_client()
    relations = SilvasoftClient.get_all(client.list_relations, IsCustomer=True)
    CachedRelation.objects.all().delete()
    for relation in relations:
        CachedRelation.objects.create(name=relation["Name"], customer_number=relation["CustomerNumber"])


def refresh_cached_products():
    client = get_silvasoft_client()
    products = SilvasoftClient.get_all(client.list_products)
    CachedProduct.objects.all().delete()
    for products in products:
        CachedProduct.objects.create(name=products["Name"], product_number=products["ArticleNumber"])
    print(CachedProduct.objects.all())
