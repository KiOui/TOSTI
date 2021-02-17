import datetime

import pytz
from django.db.models import Q
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied, ParseError, ValidationError as RestValidationError
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    RetrieveDestroyAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from orders import services
from tosti.api.permissions import HasPermissionOnObject
from orders.api.v1.serializers import OrderSerializer, ShiftSerializer, ProductSerializer
from orders.exceptions import OrderException
from orders.models import Order, Shift, Product
from orders.services import Cart, increase_shift_time, increase_shift_capacity, add_user_orders
from tosti import settings
from tosti.api.openapi import CustomAutoSchema


class CartOrderAPIView(APIView):
    """
    Cart Order API View.

    Permission required: orders.can_order_in_venue

    Use this API endpoint to order a list of Products in one go. The list of Products should be set as an array of
    Product id's in the "cart" POST parameter.
    """

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"cart": {"type": "array", "example": "[1,2,3]"}}}
    )
    permission_required = "orders.can_order_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def _extract_cart(self):
        """
        Extract the cart items from the POST data.

        :return: a Cart object with the cart items as specified in the cart in the POST data. Raises a ValidationError
        when there is not cart in the POST data. Raises a ParseError when the cart can not be parsed.
        """
        cart_as_id_list = self.request.data.get("cart", None)
        if cart_as_id_list is None:
            raise RestValidationError

        try:
            return Cart.from_list(cart_as_id_list)
        except ValueError:
            raise ParseError

    def post(self, request, **kwargs):
        """
        Create multiple Orders in one go.

        Permission required: orders.can_order_in_venue

        API endpoint for creating multiple orders in one go (handling of a cart).
        A "cart" POST parameter must be specified including the ID's of the Products the user wants to order.
        """
        shift = self.kwargs.get("shift")
        try:
            cart = self._extract_cart()
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            add_user_orders(cart.get_item_list(), shift, request.user)
        except OrderException as e:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"detail": e.__str__()})
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

        Permission required: orders.can_manage_shift_in_venue

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

    def create(self, request, *args, **kwargs):
        """Catch the OrderException that might be thrown by creating a new Order."""
        try:
            return super(OrderListCreateAPIView, self).create(request, *args, **kwargs)
        except OrderException as e:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"detail": e.__str__()})


class OrderRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    """
    Order Retrieve Destroy API View.

    Permission required: orders.can_order_in_venue
    """

    serializer_class = OrderSerializer
    permission_required = "orders.can_order_in_venue"
    permission_classes = [HasPermissionOnObject]
    queryset = Order.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        Destroy an order.

        Permission required: orders.can_manage_shift_in_venue
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
    """Shift List Create API View."""

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

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for creating a Shift.
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

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for updating a Shift.
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


class ShiftAddTimeAPIView(APIView):
    """Shift Add Time API View."""

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"minutes": {"type": "int", "example": "5"}}},
        response_schema={"$ref": "#/components/schemas/Shift"}
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Shift Add Time API View.

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for adding an amount of minutes to the end of a Shift.
        Optionally a "minutes" PATCH parameter can be set indicating with how many minutes the time should be extended.
        """
        shift = kwargs.get("shift")
        time_minutes = request.data.get("minutes", 5)
        try:
            increase_shift_time(shift, time_minutes)
            return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)
        except ValueError as e:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"detail": e.__str__()})


class ShiftAddCapacityAPIView(APIView):
    """Shift Add Capacity API View."""

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"capacity": {"type": "int", "example": "5"}}},
        response_schema={"$ref": "#/components/schemas/Shift"}
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Shift Add Capacity API View.

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for adding capacity to a Shift.
        Optionally a "capacity" PATCH parameter can be set indicating how many capacity should be added.
        """
        shift = kwargs.get("shift")
        time_minutes = request.data.get("capacity", 5)
        increase_shift_capacity(shift, time_minutes)
        return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)


class ShiftFinalizeAPIView(APIView):
    """Shift Finalize API View."""

    schema = CustomAutoSchema(
        response_schema={"$ref": "#/components/schemas/Shift"}
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Finalize a Shift.

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for finalizing a Shift.
        """
        shift = kwargs.get("shift")
        if shift.finalized:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"detail": "Shift was already finalized."})
        try:
            shift.finalized = True
            shift.save()
        except DjangoValidationError as e:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"detail": ", ".join(e.messages)})
        return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)


class ProductSearchAPIView(APIView):
    """Product Search API View."""

    serializer_class = ProductSerializer
    schema = CustomAutoSchema(
        manual_operations=[{"name": "query", "in": "query", "required": True, "schema": {"type": "string"}}],
        response_schema={"type": "array", "items": {"$ref": "#/components/schemas/Product"}},
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def get(self, request, **kwargs):
        """
        Product Search API View.

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for searching products.
        A "query" GET parameter should be specified indicating the product or barcode search query.
        """
        query = request.GET.get("query")
        if query is not None:
            string_query = services.query_product_name(query)
            barcode_query = services.query_product_barcode(query)
            all_query = set(string_query)
            all_query.update(barcode_query)
            all_query = list(all_query)
        else:
            all_query = []
        return Response(
            status=status.HTTP_200_OK,
            data=self.serializer_class(all_query, many=True, context={"request": request}).data,
        )


class ShiftScannerAPIView(APIView):
    """Shift Scanner API View."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"barcode": {"type": "string", "example": "string"}}},
        response_schema={"$ref": "#/components/schemas/Order"},
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def post(self, request, **kwargs):
        """
        Shift Scanner API View.

        Permission required: orders.can_manage_shift_in_venue

        API endpoint for adding a scanned order to a Shift.
        A "barcode" POST parameter should be specified indicating the barcode of the product to add.
        """
        shift = kwargs.get("shift")
        barcode = request.data.get("barcode", None)
        try:
            product = Product.objects.get(barcode=barcode, available=True, available_at=shift.venue)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        order = Order.objects.create(shift=shift, product=product, type=Order.TYPE_SCANNED, paid=True, ready=True)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(order, context={"request": request}).data
        )


class OrderTogglePaidAPIView(APIView):
    """Order Toggle Paid API View."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Order"})
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Order Toggle Paid API view.

        Permission required: orders.can_manage_shift_in_venue

        This toggles the paid option on an Order. Will return the Order object afterwards. If the Order does not exist
        within the Shift a 404 will be returned.
        """
        shift = kwargs.get("shift")
        order = kwargs.get("order")
        if order in Order.objects.filter(shift=shift):
            order.paid = not order.paid
            order.save()
            return Response(
                status=status.HTTP_200_OK,
                data=self.serializer_class(order, many=False, context={"request": request}).data,
            )
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class OrderToggleReadyAPIView(APIView):
    """Order Toggle Ready API View."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Order"})
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Order Toggle Ready API view.

        Permission required: orders.can_manage_shift_in_venue

        This toggles the ready option on an Order. Will return the Order object afterwards. If the Order does not exist
        within the Shift a 404 will be returned.
        """
        shift = kwargs.get("shift")
        order = kwargs.get("order")
        if order in Order.objects.filter(shift=shift):
            order.ready = not order.ready
            order.save()
            return Response(
                status=status.HTTP_200_OK, data=OrderSerializer(order, many=False, context={"request": request}).data,
            )
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
