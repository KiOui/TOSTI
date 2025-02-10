import logging
import urllib.parse

import requests
from constance import config

from borrel.models import BorrelReservation
from orders.models import Shift, Order
from silvasoft.models import (
    CachedRelation,
    CachedProduct,
    SilvasoftOrderVenue,
    SilvasoftOrderProduct,
    SilvasoftAssociation,
    SilvasoftBorrelProduct,
)

logger = logging.getLogger(__name__)


MAX_ORDER_LINES_PER_ORDER = 75


class SilvasoftException(Exception):
    """Silvasoft Exception."""

    def __init__(self, response=None):
        """Initialize the Silvasoft Exception."""
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
        """Add username and API key to requests."""
        return {"ApiKey": self.api_key, "Username": self.username}

    def get(self, path, **kwargs):
        """Send a GET request."""
        headers = self.get_authentication_headers()
        headers["Content-Type"] = "application/json"
        parameters_dict = kwargs.pop("url_parameters", {})
        parameters = urllib.parse.urlencode(parameters_dict)
        path = "{}?{}".format(path, parameters)
        response = requests.get(path, headers=headers, **kwargs)
        if response.status_code != 200:
            raise SilvasoftException(response=response)
        else:
            return response.json()

    @staticmethod
    def get_all(func, max_per_iteration=50, *args, **kwargs):
        """Use Limit and Offset parameters to get all items of an endpoint."""
        start = 0
        zero_results = False
        all_results = []
        parameters_dict = kwargs.pop("url_parameters", {})
        get_parameters = {
            "Sorting": "createdDate",
            "SortDir": "DEC",
        }
        get_parameters.update(parameters_dict)
        while not zero_results:
            get_parameters.update(Limit=max_per_iteration, Offset=start)
            results = func(url_parameters=get_parameters, *args, **kwargs)
            all_results = all_results + results
            start = start + max_per_iteration
            if len(results) != max_per_iteration:
                zero_results = True
        return all_results

    def post(self, path, **kwargs):
        """Send a POST request."""
        headers = self.get_authentication_headers()
        headers["Content-Type"] = "application/json"
        response = requests.post(path, headers=headers, **kwargs)
        if response.status_code != 200:
            raise SilvasoftException(response=response)
        else:
            return response.json()

    def list_relations(self, **kwargs):
        """List relations request."""
        return self.get(self.list_relations_url, **kwargs)

    def list_products(self, **kwargs):
        """List products request."""
        return self.get(self.list_products_url, **kwargs)

    def add_sales_invoice(self, **kwargs):
        """Add sales invoice request."""
        return self.post(self.add_sales_invoice_url, **kwargs)

    @property
    def list_relations_url(self):
        """Get list relations URL."""
        return self.get_api_url("listrelations/")

    @property
    def list_products_url(self):
        """Get list products URL."""
        return self.get_api_url("listproducts/")

    @property
    def add_sales_invoice_url(self):
        """Add sales invoice URL."""
        return self.get_api_url("addsalesinvoice/")


def get_silvasoft_client() -> SilvasoftClient:
    """Get the default Silvasoft client (with the login credentials in the Django settings file)."""
    if SilvasoftClient.can_create_client():
        return SilvasoftClient(config.SILVASOFT_API_URL, config.SILVASOFT_USERNAME, config.SILVASOFT_API_KEY)
    else:
        raise SilvasoftException(
            "SilvasoftClient could not be created, please provide valid settings for Silvasoft to function."
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


def synchronize_shift_to_silvasoft(shift: Shift, silvasoft_identifier):
    """
    Synchronize all Orders of a Shift to a Silvasoft client.

    :param shift: the Shift to synchronize all Orders of
    :type shift: Shift
    :param silvasoft_identifier: the identifier for Silvasoft
    :return: True if synchronization succeeded
    """
    try:
        silvasoft_order_venue = SilvasoftOrderVenue.objects.get(order_venue=shift.venue)
    except SilvasoftOrderVenue.DoesNotExist:
        raise SilvasoftException(
            "No Silvasoft client for {} exists, if you want to automatically synchronize shifts to Silvasoft,"
            " please add a SilvasoftOrderVenue for it.".format(shift.venue)
        )

    try:
        silvasoft_client = get_silvasoft_client()
    except SilvasoftException as e:
        raise SilvasoftException(
            "Synchronization for Shift {} failed due to an Exception while initializing the Silvasoft Client. The "
            "following Exception occurred: {}".format(shift, e)
        )

    orders = Order.objects.filter(shift=shift)
    order_lines = []
    for product, order_list in sort_orders_by_product(orders).items():
        try:
            silvasoft_order_product = SilvasoftOrderProduct.objects.get(product=product)
        except SilvasoftOrderProduct.DoesNotExist:
            raise SilvasoftException(
                "Skipping Silvasoft synchronization for Shift {} as one of the Products ({}) is not connected"
                "to any Silvasoft Product.".format(shift, product)
            )

        order_line_to_append = {
            "ProductNumber": silvasoft_order_product.silvasoft_product_number,
            "Quantity": len(order_list),
            "UseArticlePrice": True,
        }

        if silvasoft_order_product.cost_center:
            order_line_to_append["CostCenter"] = silvasoft_order_product.cost_center

        order_lines.append(order_line_to_append)

    if len(order_lines) > 75:
        raise SilvasoftException(
            "Synchronization for Shift {} failed because the invoice has more than 75 line items and this is not "
            "supported by Silvasoft.".format(shift)
        )

    silvasoft_client.add_sales_invoice(
        json={
            "CustomerNumber": silvasoft_order_venue.silvasoft_customer_number,
            "InvoiceNotes": "Shift #{}<br>Date: {}<br>Synchronisation ID: {}".format(
                shift.id, shift.start.strftime("%d-%m-%Y"), silvasoft_identifier
            ),
            "Invoice_InvoiceLine": order_lines,
        }
    )


def synchronize_borrelreservation_to_silvasoft(borrel_reservation: BorrelReservation, silvasoft_identifier):
    """Synchronize a Borrel Reservation to Silvasoft."""
    if borrel_reservation.association is None:
        raise SilvasoftException("No association set for {}.".format(borrel_reservation))

    try:
        silvasoft_association = SilvasoftAssociation.objects.get(association=borrel_reservation.association)
    except SilvasoftAssociation.DoesNotExist:
        raise SilvasoftException(
            "No Silvasoft client for {} exists, if you want to automatically synchronize borrel reservations to "
            "Silvasoft, please add a SilvasoftAssociation for it.".format(borrel_reservation.association)
        )

    try:
        silvasoft_client = get_silvasoft_client()
    except SilvasoftException as e:
        raise SilvasoftException(
            "Synchronization for Borrel Reservation {} failed due to an Exception while initializing the Silvasoft "
            "Client. The following Exception occurred: {}".format(borrel_reservation, e)
        )

    order_lines = []
    for reservation_item in borrel_reservation.items.filter(product__can_be_submitted=True):
        if reservation_item.amount_used is None:
            raise SilvasoftException(
                "The amount used for {} is not filled in yet, please register how much is used for {} and then rerun "
                "synchronization.".format(reservation_item.product, reservation_item.product)
            )

        if reservation_item.amount_used == 0:
            continue

        try:
            silvasoft_borrel_product = SilvasoftBorrelProduct.objects.get(product=reservation_item.product)
        except SilvasoftBorrelProduct.DoesNotExist:
            raise SilvasoftException(
                "No Silvasoft Borrel Product exists for {}, if you want to automatically synchronize to Silvasoft,"
                " please add a Silvasoft Borrel Product for it.".format(reservation_item.product)
            )

        order_line_to_append = {
            "ProductNumber": silvasoft_borrel_product.silvasoft_product_number,
            "Quantity": reservation_item.amount_used,
            "UseArticlePrice": True,
        }

        if silvasoft_borrel_product.cost_center:
            order_line_to_append["CostCenter"] = silvasoft_borrel_product.cost_center

        order_lines.append(order_line_to_append)

    if len(order_lines) > 75:
        raise SilvasoftException(
            "Synchronization for Borrel Reservation {} failed because the invoice has more than 75 line items and this"
            " is not supported by Silvasoft.".format(borrel_reservation)
        )

    silvasoft_client.add_sales_invoice(
        json={
            "CustomerNumber": silvasoft_association.silvasoft_customer_number,
            "InvoiceNotes": "Borrel reservation: {}<br>Date: {}<br>Responsible: {}<br>Synchronisation ID: {}".format(
                borrel_reservation.title,
                borrel_reservation.start.strftime("%d-%m-%Y"),
                borrel_reservation.user_submitted,
                silvasoft_identifier,
            ),
            "Invoice_InvoiceLine": order_lines,
        }
    )


def refresh_cached_relations():
    """Refresh the relations cached in TOSTI."""
    client = get_silvasoft_client()
    relations = SilvasoftClient.get_all(client.list_relations, url_parameters={"IsCustomer": True})
    CachedRelation.objects.all().delete()
    for relation in relations:
        CachedRelation.objects.create(name=relation["Name"], customer_number=relation["CustomerNumber"])


def refresh_cached_products():
    """Refresh the products cached in TOSTI."""
    client = get_silvasoft_client()
    products = SilvasoftClient.get_all(client.list_products)
    CachedProduct.objects.all().delete()
    for product in products:
        if product["ArticleNumber"] is not None:
            CachedProduct.objects.create(name=product["Name"], product_number=product["ArticleNumber"])
