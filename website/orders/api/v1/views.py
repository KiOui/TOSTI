import datetime

import django_filters.rest_framework
import pytz
from django.contrib.admin.models import CHANGE, ADDITION
from django.db.models import Q
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
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
from tosti.api.views import LoggedRetrieveUpdateAPIView, LoggedListCreateAPIView, LoggedRetrieveDestroyAPIView
from tosti.utils import log_action


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
    queryset = Order.objects.select_related("user", "product")

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(shift=self.kwargs.get("shift")).order_by("-prioritize", "created")

    def get_serializer_context(self):
        """Add shift to serializer context."""
        return {"shift": self.kwargs.get("shift")}

    def perform_create(self, serializer):
        """Create an order, either as ordering users or as managers."""
        shift = self.kwargs.get("shift")
        if user_can_manage_shift(self.request.user, shift):
            # Save the order as it was passed to the API as the user has permission to save orders for all users in
            # the shift
            order = serializer.save(shift=shift, user=self.request.user)
            log_action(self.request.user, order, CHANGE, "Created order as manager via API.")
        else:
            # Save the order while ignoring the order_type, user, paid and ready argument as the user does not have
            # permissions to save orders for all users in the shift
            order = serializer.save(
                shift=shift, type=Order.TYPE_ORDERED, user=self.request.user, paid=False, ready=False
            )
            log_action(self.request.user, order, CHANGE, "Created order via API.")

    def create(self, request, *args, **kwargs):
        """Catch the OrderException that might be thrown by creating a new Order."""
        try:
            return super(OrderListCreateAPIView, self).create(request, *args, **kwargs)
        except OrderException as e:
            raise PermissionDenied(detail=e.__str__())


class OrderRetrieveDestroyAPIView(LoggedRetrieveDestroyAPIView):
    """API View to retrieve and destroy orders."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "DELETE": ["orders:manage"],
    }

    queryset = Order.objects.select_related("user", "product")

    def destroy(self, request, *args, **kwargs):
        """Destroy an order."""
        shift = kwargs.get("shift")
        if not user_can_manage_shift(request.user, shift):
            raise PermissionDenied
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """Get the queryset."""
        return self.queryset.filter(shift=self.kwargs.get("shift"))


class ShiftListCreateAPIView(LoggedListCreateAPIView):
    """API View to list and create shifts."""

    serializer_class = ShiftSerializer
    queryset = Shift.objects.select_related("venue__venue").prefetch_related("assignees")
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


class ShiftRetrieveUpdateAPIView(LoggedRetrieveUpdateAPIView):
    """API View to retrieve and update a shift."""

    serializer_class = ShiftSerializer
    queryset = Shift.objects.prefetch_related("assignees")
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
            log_action(
                self.request.user, shift, CHANGE, f"Extended shift's end time with {time_minutes} minutes via API."
            )
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
            log_action(self.request.user, shift, CHANGE, f"Added {capacity} to shift's capacity via API.")
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
            log_action(self.request.user, shift, CHANGE, "Finalized shift via API.")
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
        log_action(self.request.user, order, ADDITION, "Created scanned order via API.")

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
        log_action(self.request.user, order, CHANGE, f"Set order paid to {order.paid} via API.")

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
        log_action(self.request.user, order, CHANGE, f"Set order ready to {order.ready} via API.")

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
            log_action(self.request.user, shift, CHANGE, "Joined shift via API.")

        except PermissionError:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(
            status=status.HTTP_200_OK, data=self.serializer_class(shift, many=False, context={"request": request}).data
        )
