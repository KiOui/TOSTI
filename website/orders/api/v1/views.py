import datetime

import django_filters.rest_framework
import pytz
from django.db.models import Q
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    RetrieveUpdateAPIView,
    RetrieveDestroyAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.api.v1.filters import ShiftFilter, OrderFilter, ProductFilter
from orders.api.v1.serializers import OrderSerializer, ShiftSerializer, ProductSerializer
from orders.exceptions import OrderException
from orders.models import Order, Shift, Product
from orders.services import (
    increase_shift_time,
    increase_shift_capacity,
    add_user_to_assignees_of_shift,
    user_can_manage_shifts_in_venue,
    user_can_manage_shift,
    add_scanned_order,
)
from tosti import settings
from tosti.api.openapi import CustomAutoSchema
from tosti.api.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class OrderListCreateAPIView(ListCreateAPIView):
    """API View to list and create orders."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
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

    def get_serializer_context(self):
        """Add shift to serializer context."""
        return {"shift": self.kwargs.get("shift")}

    def perform_create(self, serializer):
        """Create an order, either as ordering users or as managers."""
        shift = self.kwargs.get("shift")
        if user_can_manage_shift(self.request.user, shift):
            # Save the order as it was passed to the API as the user has permission to save orders for all users in
            # the shift
            serializer.save(shift=shift, user=self.request.user)
        else:
            # Save the order while ignoring the order_type, user, paid and ready argument as the user does not have
            # permissions to save orders for all users in the shift
            serializer.save(shift=shift, type=Order.TYPE_ORDERED, user=self.request.user, paid=False, ready=False)

    def create(self, request, *args, **kwargs):
        """Catch the OrderException that might be thrown by creating a new Order."""
        try:
            return super(OrderListCreateAPIView, self).create(request, *args, **kwargs)
        except OrderException as e:
            raise PermissionDenied(detail=e.__str__())


class OrderRetrieveDestroyAPIView(RetrieveDestroyAPIView):
    """API View to retrieve and destroy orders."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "DELETE": ["orders:manage"],
    }

    queryset = Order.objects.all()

    def destroy(self, request, *args, **kwargs):
        """Destroy an order."""
        shift = kwargs.get("shift")
        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(shift=self.kwargs.get("shift"))


class ShiftListCreateAPIView(ListCreateAPIView):
    """API View to list and create shifts."""

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
        """Create a shift."""
        venue = request.data.get("venue")
        if not user_can_manage_shifts_in_venue(request.user, venue):
            raise PermissionDenied
        return super().create(request, *args, **kwargs)


class ShiftRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    """API View to retrieve and update a shift."""

    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "PUT": ["orders:manage"],
        "PATCH": ["orders:manage"],
    }

    def update(self, request, *args, **kwargs):
        """Update a shift."""
        shift = get_object_or_404(Shift, pk=kwargs.get("pk"))
        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied
        return super().update(request, *args, **kwargs)


class ProductListAPIView(ListAPIView):
    """List all available products."""

    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["read"]
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    )
    filter_class = ProductFilter
    search_fields = ["name", "barcode"]

    def get_queryset(self):
        """
        Get the queryset.

        The following piece of code is to circumvent a warning generated by API schema generation.
        """
        shift = self.kwargs.get("shift")
        if shift is not None:
            return self.queryset.filter(available_at=shift.venue)
        else:
            return self.queryset.filter(available_at=None)


class ShiftAddTimeAPIView(APIView):
    """API View to extend the end time of a shift."""

    serializer_class = ShiftSerializer
    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"minutes": {"type": "int", "example": "5"}}},
        response_schema={"$ref": "#/components/schemas/Shift"},
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def patch(self, request, **kwargs):
        """Extend the end time of a shift based on an optional `minutes` PATCH parameter."""
        shift = kwargs.get("shift")
        time_minutes = request.data.get("minutes", 5)
        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied

        try:
            increase_shift_time(shift, time_minutes)
            return Response(
                status=status.HTTP_200_OK, data=self.serializer_class(shift, context={"request": request}).data
            )
        except DjangoValidationError as e:
            raise PermissionDenied(detail=e.__str__())


class ShiftAddCapacityAPIView(APIView):
    """API View to increase the capacity of a shift."""

    serializer_class = ShiftSerializer
    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"capacity": {"type": "int", "example": "5"}}},
        response_schema={"$ref": "#/components/schemas/Shift"},
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def patch(self, request, **kwargs):
        """Increase the capacity of a shift based on an optional `capacity` PATCH parameter."""
        shift = kwargs.get("shift")
        capacity = request.data.get("capacity", 5)
        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied

        try:
            increase_shift_capacity(shift, capacity)
            return Response(
                status=status.HTTP_200_OK, data=self.serializer_class(shift, context={"request": request}).data
            )
        except DjangoValidationError as e:
            raise PermissionDenied(detail=e.__str__())


class ShiftFinalizeAPIView(APIView):
    """API View to finalize a shift."""

    serializer_class = ShiftSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Shift"})
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def patch(self, request, **kwargs):
        """Finalize a shift."""
        shift = kwargs.get("shift")
        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied

        if shift.finalized:
            return Response(status=status.HTTP_403_FORBIDDEN, data={"detail": "Shift was already finalized."})
        try:
            shift.finalized = True
            shift.save()
        except DjangoValidationError as e:
            raise PermissionDenied(detail=", ".join(e.messages))

        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(shift, context={"request": request}).data
        )


class ShiftScannerAPIView(APIView):
    """API View to add scanned products."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"barcode": {"type": "string", "example": "string"}}},
        response_schema={"$ref": "#/components/schemas/Order"},
    )
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def post(self, request, **kwargs):
        """Add a scanned product based on a `barcode` POST parameter."""
        shift = kwargs.get("shift")
        barcode = request.data.get("barcode", None)
        try:
            product = Product.objects.get(barcode=barcode, available=True, available_at=shift.venue)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied

        order = add_scanned_order(product, shift)

        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(order, context={"request": request}).data
        )


class OrderTogglePaidAPIView(APIView):
    """API View to change the paid status of orders."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Order"})
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def patch(self, request, **kwargs):
        """Toggle the order paid status."""
        shift = kwargs.get("shift")
        order = kwargs.get("order")

        if order not in Order.objects.filter(shift=shift):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied

        order.paid = not order.paid
        order.save()
        return Response(
            status=status.HTTP_200_OK,
            data=OrderSerializer(order, many=False, context={"request": request}).data,
        )


class OrderToggleReadyAPIView(APIView):
    """API View to change the ready status of orders."""

    serializer_class = OrderSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Order"})
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def patch(self, request, **kwargs):
        """Toggle the order ready status."""
        shift = kwargs.get("shift")
        order = kwargs.get("order")

        if order not in Order.objects.filter(shift=shift):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied

        order.ready = not order.ready
        order.save()
        return Response(
            status=status.HTTP_200_OK,
            data=OrderSerializer(order, many=False, context={"request": request}).data,
        )


class JoinShiftAPIView(APIView):
    """API View to join the assignees of a shift."""

    serializer_class = ShiftSerializer
    schema = CustomAutoSchema(response_schema={"$ref": "#/components/schemas/Shift"})
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["orders:manage"]

    def patch(self, request, **kwargs):
        """Join the shift assignees."""
        shift = kwargs.get("shift")
        if not user_can_manage_shifts_in_venue(request.user, shift.venue):
            raise PermissionDenied
        try:
            add_user_to_assignees_of_shift(request.user, shift)
        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(shift, many=False, context={"request": request}).data
        )
