import datetime

import django_filters.rest_framework
import pytz
from django.contrib.admin.models import CHANGE, ADDITION
from django.db.models import Q
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import status, filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    get_object_or_404,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.api.v1.filters import ShiftFilter, OrderFilter, ProductFilter
from orders.api.v1.serializers import OrderSerializer, ShiftSerializer, ProductSerializer, OrderVenueSerializer
from orders.exceptions import OrderException
from orders.models import Order, Shift, Product, OrderVenue
from orders.services import (
    user_can_manage_shifts_in_venue,
    user_can_manage_shift,
    add_scanned_order,
)
from tosti import settings
from tosti.api.openapi import CustomAutoSchema
from tosti.api.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from tosti.api.v1.pagination import StandardResultsSetPagination
from tosti.api.views import LoggedRetrieveUpdateAPIView, LoggedListCreateAPIView, LoggedRetrieveUpdateDestroyAPIView
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
    filterset_class = OrderFilter
    queryset = Order.objects.select_related("user", "product")

    def get_queryset(self):
        """Get the queryset."""
        return (
            self.queryset.filter(shift=self.kwargs.get("shift"))
            .prefetch_related("user_association", "user__association")
            .order_by("-priority", "created")
        )

    def get_serializer_context(self):
        """Add shift to serializer context."""
        return {"shift": self.kwargs.get("shift")}

    def perform_create(self, serializer):
        """Create an order, either as ordering users or as managers."""
        shift = self.kwargs.get("shift")
        if user_can_manage_shift(self.request.user, shift):
            # Save the order as it was passed to the API as the user has permission to save orders for all users in
            # the shift.
            order = serializer.save(shift=shift, user=self.request.user)
            log_action(self.request.user, order, CHANGE, "Created order as manager via API.")
        else:
            # Save the order while ignoring the order_type, user, paid and ready argument as the user does not have
            # permissions to save orders for all users in the shift.
            order = serializer.save(
                shift=shift, type=Order.TYPE_ORDERED, user=self.request.user, paid=False, ready=False
            )
            log_action(self.request.user, order, CHANGE, "Created order via API.")

    def create(self, request, *args, **kwargs):
        """Catch the OrderException that might be thrown by creating a new Order."""
        shift = kwargs.get("shift")
        priority = request.data.get("priority")
        if not user_can_manage_shift(self.request.user, shift) and priority is Order.PRIORITY_PRIORITIZED:
            # Users that can't manage the shift should not be able to create a prioritized order.
            raise PermissionDenied(detail="You are not allowed to create prioritized orders!")

        try:
            return super(OrderListCreateAPIView, self).create(request, *args, **kwargs)
        except OrderException as e:
            raise PermissionDenied(detail=e.__str__())


class OrderRetrieveUpdateDestroyAPIView(LoggedRetrieveUpdateDestroyAPIView):
    """API View to retrieve and destroy orders."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["orders:order"],
        "PATCH": ["orders:order"],
        "PUT": ["orders:manage"],
        "DELETE": ["orders:manage"],
    }
    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {
                "ready": {"type": "boolean"},
                "paid": {"type": "boolean"},
                "priority": {"type": "number"},
            },
        }
    )

    queryset = Order.objects.select_related("user", "product")

    def put(self, request, *args, **kwargs):
        """PUT is only available for shift managers."""
        shift = self.kwargs.get("shift")
        if user_can_manage_shift(request.user, shift):
            return super().put(request, *args, **kwargs)
        else:
            self.permission_denied(request)

    def update(self, request, *args, **kwargs):
        """Update an order."""
        instance = self.get_object()
        shift = self.kwargs.get("shift")
        if user_can_manage_shift(self.request.user, shift):
            # All changeable order fields can be changed by the user.
            return super().update(request, *args, **kwargs)
        else:
            # Users can only change their own orders.
            if instance.user != request.user:
                self.permission_denied(
                    request, message="You don't have permission to alter other people's orders.", code=403
                )

            # Only priority can be changed by the user.
            priority = request.data.get("priority", None)

            if priority is not None and priority == Order.PRIORITY_DEPRIORITIZED:
                # User wants to set their order to deprioritized.
                serializer = self.get_serializer(
                    instance, data={"priority": Order.PRIORITY_DEPRIORITIZED}, partial=True
                )
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            else:
                self.permission_denied(
                    request, message="Only the priority option can be changed to deprioritized.", code=400
                )

    def destroy(self, request, *args, **kwargs):
        """Destroy an order."""
        shift = kwargs.get("shift")
        if not user_can_manage_shift(request.user, shift):
            self.permission_denied(request)
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
    filterset_class = ShiftFilter
    pagination_class = StandardResultsSetPagination

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
        venue = OrderVenue.objects.get(pk=venue)
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
    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {
                "start": {"type": "string", "format": "date-time"},
                "end": {"type": "string", "format": "date-time"},
                "can_order": {"type": "boolean"},
                "finalized": {"type": "boolean"},
                "max_orders_per_user": {"type": "integer", "nullable": True},
                "max_orders_total": {"type": "integer", "nullable": True},
                "assignees": {"type": "array", "items": {"type": "integer"}},
            },
        }
    )

    def update(self, request, *args, **kwargs):
        """Update a shift."""
        shift = get_object_or_404(Shift, pk=kwargs.get("pk"))
        if not user_can_manage_shift(request.user, shift):
            self.permission_denied(request)
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
    filterset_class = ProductFilter
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


class OrderVenueListAPIView(ListAPIView):
    """API View to list Order Venues."""

    serializer_class = OrderVenueSerializer
    queryset = OrderVenue.objects.all()
