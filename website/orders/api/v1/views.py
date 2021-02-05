import datetime

import pytz
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, schema
from rest_framework.exceptions import PermissionDenied, ParseError, ValidationError
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    RetrieveDestroyAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from orders import services
from orders.api.v1.permissions import HasPermissionOnObject
from orders.api.v1.serializers import OrderSerializer, ShiftSerializer, ProductSerializer
from orders.exceptions import OrderException
from orders.models import Order, Shift, Product
from orders.services import Cart, place_orders, increase_shift_time, increase_shift_capacity
from tosti import settings


class CartOrderAPIView(APIView):
    """
    Cart Order API View.

    Permission required: shift.can_order_in_venue

    Use this API endpoint to order a list of Products in one go. The list of Products should be set as an array of
    Product id's in the "cart" POST parameter.
    """

    def _extract_cart(self):
        """
        Extract the cart items from the POST data.

        :return: a Cart object with the cart items as specified in the cart in the POST data. Raises a ValidationError
        when there is not cart in the POST data. Raises a ParseError when the cart can not be parsed.
        """
        cart_as_id_list = self.request.data.get("cart", None)
        if cart_as_id_list is None:
            raise ValidationError

        try:
            return Cart.from_list(cart_as_id_list)
        except ValueError:
            raise ParseError

    def get_object(self):
        """
        Get the Shift the user wants to add the orders to.

        :return: a Shift object
        """
        return self.kwargs.get("shift")

    def post(self, request, **kwargs):
        """
        Create multiple Orders in one go.

        API endpoint for creating multiple orders in one go (handling of a cart).
        A "cart" POST parameter must be specified including the ID's of the Products the user wants to order.
        Permission required: can_order_in_venue
        :param request: the request
        :param kwargs: keyword arguments
        :return: a 201 response code if all orders in the cart were successfully processed. Raises a ValidationError
        if some Orders in the cart can not be processed. Returns a 400 response code if the cart could not be read or
        is not present in the POST data, raises a PermissionDenied error when the user does not have permission
        """
        shift = self.get_object()
        if not self.request.user.has_perm("orders.can_order_in_venue", shift.venue):
            raise PermissionDenied

        try:
            cart = self._extract_cart()
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            place_orders(cart.get_item_list(), request.user, shift)
        except OrderException as e:
            raise ValidationError(e.__str__())
        return Response(status=status.HTTP_200_OK)


class OrderListCreateAPIView(ListCreateAPIView):
    """
    Order List Create API View.

    Permission required: None

    Use this API view to list all Orders within a Shift. Order objects can also be created individually using a POST
    to this API view.
    """

    serializer_class = OrderSerializer
    permission_required = "orders.can_order_in_venue"
    permission_classes = [HasPermissionOnObject]
    queryset = Order.objects.all()

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(shift=self.kwargs.get("shift"))

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def perform_create(self, serializer):
        """
        Perform the creation of a new Order.

        This method actually checks if the user has manage permissions in the shift and else ignores the order_type,
        paid and ready fields.
        :param serializer: the serializer
        :type serializer: OrderSerializer
        :return: None
        :rtype: None
        """
        shift = self.kwargs.get("shift")
        if self.request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
            # Save the order as it was passed to the API as the user has permission to save orders for all users in
            # the shift
            serializer.save(shift=shift, user=self.request.user)
        else:
            # Save the order while ignoring the order_type, user, paid and ready argument as the user does not have
            # permissions to save orders for all users in the shift
            serializer.save(
                shift=shift, order_type=Order.TYPE_ORDERED, user=self.request.user, paid=False, ready=False
            )


class OrderRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    """
    Order Retrieve Destroy API View.

    Permission required: orders.can_order_in_venue
    For destroying an Order, the orders.can_manage_shift_in_venue permission is required.
    """

    serializer_class = OrderSerializer
    permission_required = "orders.can_order_in_venue"
    permission_classes = [HasPermissionOnObject]
    queryset = Order.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        Destroy an order.

        This method needs the orders.can_manage_shift_in_venue permission
        """
        if self.request.user.has_perm("orders.can_manage_shift_in_venue", self.kwargs.get("shift").venue):
            return super().destroy(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(shift=self.kwargs.get("shift"))

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue


class ShiftListCreateAPIView(ListCreateAPIView):
    """
    Shift List Create API View.

    Permission required: orders.can_manage_shift_in_venue
    """

    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()

    def get_queryset(self):
        """Get the queryset."""
        active = self.request.query_params.get("active", None)
        if active is not None:
            active = active == "true"
            timezone = pytz.timezone(settings.TIME_ZONE)
            current_time = timezone.localize(datetime.datetime.now())
            if active:
                return self.queryset.filter(start_date__lte=current_time, end_date__gte=current_time)
            else:
                return self.queryset.filter(Q(start_date__gte=current_time) | Q(end_date__lte=current_time))
        else:
            return self.queryset.all()

    def create(self, request, *args, **kwargs):
        """
        Create a Shift.

        API endpoint for creating a Shift.
        Permission required: can_manage_shift_in_venue
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied when 'venue' POST data is None or when user does not have permission
        in indicated venue
        """
        venue = request.data.get("venue")
        if request.user.has_perm("orders.can_manage_shift_in_venue", venue):
            return super().create(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ShiftRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """
    Shift Retrieve Update API View.

    Permission required: orders.can_manage_shift_in_venue (for the update method)
    """

    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()

    def update(self, request, *args, **kwargs):
        """
        Update a Shift.

        API endpoint for updating a Shift.
        Permission required: can_manage_shift_in_venue
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied when 'venue' POST data is None or when user does not have permission
        in indicated venue
        """
        venue = request.data.get("venue")
        if request.user.has_perm("orders.can_manage_shift_in_venue", venue):
            return super().update(request, *args, **kwargs)
        else:
            raise PermissionDenied


class ProductListAPIView(ListAPIView):
    """
    Product list API View.

    Permission required: None
    """

    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(available_at=self.kwargs.get("shift").venue)


@api_view(["PATCH"])
def shift_add_time(request, **kwargs):
    """
    Shift Add Time API View.

    Permission required: can_manage_shift_in_venue

    API endpoint for adding an amount of minutes to the end of a Shift.
    Optionally a "minutes" PATCH parameter can be set indicating with how many minutes the time should be extended.
    """
    shift = kwargs.get("shift")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        time_minutes = request.data.get("minutes", 5)
        increase_shift_time(shift, time_minutes)
        return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def shift_add_capacity(request, **kwargs):
    """
    Shift Add Capacity API View.

    Permission required: can_manage_shift_in_venue

    API endpoint for adding capacity to a Shift.
    Optionally a "capacity" PATCH parameter can be set indicating how many capacity should be added.
    """
    shift = kwargs.get("shift")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        time_minutes = request.data.get("capacity", 5)
        increase_shift_capacity(shift, time_minutes)
        return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)
    else:
        raise PermissionDenied


@api_view(["POST"])
def shift_scanner(request, **kwargs):
    """
    Shift Scanner API View.

    Permission required: can_manage_shift_in_venue

    API endpoint for adding a scanned order to a Shift.
    A "barcode" POST parameter should be specified indicating the barcode of the product to add.
    """
    shift = kwargs.get("shift")
    barcode = request.data.get("barcode", None)
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        try:
            product = Product.objects.get(barcode=barcode, available=True, available_at=shift.venue)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        order = Order.objects.create(shift=shift, product=product, type=Order.TYPE_SCANNED, paid=True, ready=True)
        return Response(status=status.HTTP_200_OK, data=OrderSerializer(order, context={"request": request}).data)
    else:
        raise PermissionDenied


@api_view(["GET"])
def product_search(request, **kwargs):
    """
    Product Search API View.

    Permission required: can_manage_shift_in_venue

    API endpoint for searching products.
    A "query" GET parameter should be specified indicating the product or barcode search query.
    """
    shift = kwargs.get("shift")
    query = request.GET.get("query")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        if query is not None:
            string_query = services.query_product_name(query)
            barcode_query = services.query_product_barcode(query)
            all_query = set(string_query)
            all_query.update(barcode_query)
            all_query = list(all_query)
        else:
            all_query = []
        return Response(
            status=status.HTTP_200_OK, data=ProductSerializer(all_query, many=True, context={"request": request}).data
        )
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def order_toggle_paid(request, **kwargs):
    """
    Order Toggle Paid API view.

    Permission required: orders.can_manage_shift_in_venue

    This toggles the paid option on an Order. Will return the Order object afterwards. If the Order does not exist
    within the Shift a 404 will be returned.
    """
    shift = kwargs.get("shift")
    order = kwargs.get("order")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        if order in Order.objects.filter(shift=shift):
            order.paid = not order.paid
            order.save()
            return Response(
                status=status.HTTP_200_OK, data=OrderSerializer(order, many=False, context={"request": request}).data
            )
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        raise PermissionDenied


@api_view(["PATCH"])
def order_toggle_ready(request, **kwargs):
    """
    Order Toggle Ready API view.

    Permission required: orders.can_manage_shift_in_venue

    This toggles the ready option on an Order. Will return the Order object afterwards. If the Order does not exist
    within the Shift a 404 will be returned.
    """
    shift = kwargs.get("shift")
    order = kwargs.get("order")
    if request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue):
        if order in Order.objects.filter(shift=shift):
            order.ready = not order.ready
            order.save()
            return Response(
                status=status.HTTP_200_OK, data=OrderSerializer(order, many=False, context={"request": request}).data
            )
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        raise PermissionDenied
