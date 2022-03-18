import datetime

import django_filters.rest_framework
import pytz
from django.db.models import Q
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
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

from orders.api.v1.filters import ShiftFilter, OrderFilter, ProductFilter
from orders.api.v1.permissions import IsOnBakersList
from orders.api.v1.serializers import OrderSerializer, ShiftSerializer, ProductSerializer
from orders.exceptions import OrderException
from orders.models import Order, Shift, Product
from orders.services import Cart, increase_shift_time, increase_shift_capacity, add_user_orders
from tosti import settings
from tosti.api.openapi import CustomAutoSchema
from tosti.api.permissions import HasPermissionOnObject, IsAuthenticatedOrTokenHasScopeForMethod


class OrderListCreateAPIView(ListCreateAPIView):
    """
    Order List Create API View.

    Permission required: None

    Use this API view to list all Orders within a Shift. Order objects can also be created individually using a POST
    to this API view.
    """

    serializer_class = OrderSerializer
    permission_required = "orders.can_order_in_venue"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "POST": ["orders:manage"],
    }
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
    ]
    filter_class = OrderFilter
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

        Permission required: orders.can_manage_shift_in_venue and user in shift assignees

        This method actually checks if the user has manage permissions in the shift and else ignores the order_type,
        paid and ready fields.
        :param serializer: the serializer
        :type serializer: OrderSerializer
        :return: None
        :rtype: None
        """
        shift = self.kwargs.get("shift")
        if (
            self.request.user.has_perm("orders.can_manage_shift_in_venue", shift.venue)
            and self.request.user in shift.get_assignees()
        ):
            # Save the order as it was passed to the API as the user has permission to save orders for all users in
            # the shift
            serializer.save(shift=shift, user=self.request.user)
        else:
            # Save the order while ignoring the order_type, user, paid and ready argument as the user does not have
            # permissions to save orders for all users in the shift
            serializer.save(
                shift=shift, type=Order.TYPE_ORDERED, user=self.request.user, paid=False, ready=False
            )

    def create(self, request, *args, **kwargs):
        """Catch the OrderException that might be thrown by creating a new Order."""
        try:
            return super(OrderListCreateAPIView, self).create(request, *args, **kwargs)
        except OrderException as e:
            raise PermissionDenied(detail=e.__str__())


class OrderRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    """
    Order Retrieve Destroy API View.

    Permission required: orders.can_order_in_venue
    """

    serializer_class = OrderSerializer
    permission_required = "orders.can_order_in_venue"
    permission_classes = [HasPermissionOnObject, IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "DELETE": ["orders:manage"],
    }

    queryset = Order.objects.all()

    def destroy(self, request, *args, **kwargs):
        """
        Destroy an order.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees
        """
        if (
            self.request.user.has_perm("orders.can_manage_shift_in_venue", self.kwargs.get("shift").venue)
            and request.user in self.kwargs.get("shift").get_assignees()
        ):
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
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "POST": ["orders:manage"],
    }
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = ShiftFilter

    def get_queryset(self):
        """Get the queryset."""
        active = self.request.query_params.get("active", None)
        if active is not None:
            active = active == "true"
            timezone = pytz.timezone(settings.TIME_ZONE)
            current_time = timezone.localize(datetime.datetime.now())
            if active:
                return self.queryset.filter(start__lte=current_time, end__gte=current_time)
            else:
                return self.queryset.filter(Q(start__gte=current_time) | Q(end__lte=current_time))
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
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "PUT": ["orders:manage"],
        "PATCH": ["orders:manage"],
    }

    def update(self, request, *args, **kwargs):
        """
        Update a Shift.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees

        API endpoint for updating a Shift.
        :param request: the request
        :param args: arguments
        :param kwargs: keyword arguments
        :return: super method or PermissionDenied when 'venue' POST data is None or when user does not have permission
        in indicated venue
        """
        venue = request.data.get("venue")
        if (
            request.user.has_perm("orders.can_manage_shift_in_venue", venue)
            and request.user in self.get_object().get_assignees()
        ):
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
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    )
    required_scopes = ["read"]
    filter_class = ProductFilter
    search_fields = ["name", "barcode"]

    def get_queryset(self):
        """Get the queryset."""
        # The following piece of code is to circumvent a warning generated by schema generation on the API
        # documentation page.
        shift = self.kwargs.get("shift")
        if shift is not None:
            return self.queryset.filter(available_at=shift.venue)
        else:
            return self.queryset.filter(available_at=None)


class ShiftAddTimeAPIView(APIView):
    """Shift Add Time API View."""

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"minutes": {"type": "int", "example": "5"}}},
        response_schema={"$ref": "#/components/schemas/Shift"},
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_shift(self):
        """Get Shift."""
        return self.kwargs.get("shift")

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Shift Add Time API View.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees

        Scopes required: `orders:manage`

        API endpoint for adding an amount of minutes to the end of a Shift.
        Optionally a "minutes" PATCH parameter can be set indicating with how many minutes the time should be extended.
        """
        shift = kwargs.get("shift")
        time_minutes = request.data.get("minutes", 5)
        try:
            increase_shift_time(shift, time_minutes)
            return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)
        except DjangoValidationError as e:
            raise PermissionDenied(detail=e.__str__())


class ShiftAddCapacityAPIView(APIView):
    """Shift Add Capacity API View."""

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"capacity": {"type": "int", "example": "5"}}},
        response_schema={"$ref": "#/components/schemas/Shift"},
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_shift(self):
        """Get Shift."""
        return self.kwargs.get("shift")

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Shift Add Capacity API View.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees

        API endpoint for adding capacity to a Shift.
        Optionally a "capacity" PATCH parameter can be set indicating how many capacity should be added.
        """
        shift = kwargs.get("shift")
        capacity = request.data.get("capacity", 5)
        try:
            increase_shift_capacity(shift, capacity)
            return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)
        except DjangoValidationError as e:
            raise PermissionDenied(detail=e.__str__())


class ShiftFinalizeAPIView(APIView):
    """Shift Finalize API View."""

    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Shift"})
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_shift(self):
        """Get Shift."""
        return self.kwargs.get("shift")

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
            raise PermissionDenied(detail=", ".join(e.messages))
        return Response(status=status.HTTP_200_OK, data=ShiftSerializer(shift, context={"request": request}).data)


class ShiftScannerAPIView(APIView):
    """Shift Scanner API View."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"barcode": {"type": "string", "example": "string"}}},
        response_schema={"$ref": "#/components/schemas/Order"},
    )
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_shift(self):
        """Get Shift."""
        return self.kwargs.get("shift")

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def post(self, request, **kwargs):
        """
        Shift Scanner API View.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees

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
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_shift(self):
        """Get Shift."""
        return self.kwargs.get("shift")

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Order Toggle Paid API view.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees

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
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_shift(self):
        """Get Shift."""
        return self.kwargs.get("shift")

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Order Toggle Ready API view.

        Permission required: orders.can_manage_shift_in_venue and user must be in shift assignees

        This toggles the ready option on an Order. Will return the Order object afterwards. If the Order does not exist
        within the Shift a 404 will be returned.
        """
        shift = kwargs.get("shift")
        order = kwargs.get("order")
        if order in Order.objects.filter(shift=shift):
            order.ready = not order.ready
            order.save()
            return Response(
                status=status.HTTP_200_OK,
                data=OrderSerializer(order, many=False, context={"request": request}).data,
            )
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class JoinShiftAPIView(APIView):
    """Join Shift API View."""

    serializer_class = ShiftSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Shift"})
    permission_required = "orders.can_manage_shift_in_venue"
    permission_classes = [HasPermissionOnObject, IsOnBakersList, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def get_permission_object(self):
        """Get the object to check permissions for."""
        obj = self.kwargs.get("shift")
        return obj.venue

    def patch(self, request, **kwargs):
        """
        Join Shift as baker view.

        Permission required: orders.can_manage_shift_in_venue

        This adds the requesting User to the Shift assignees.
        """
        shift = kwargs.get("shift")
        try:
            shift.assignees.add(request.user.id)
            shift.save()
        except ValueError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(shift, many=False, context={"request": request}).data
        )
