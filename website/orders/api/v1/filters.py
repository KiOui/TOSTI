from django_filters import IsoDateTimeFilter
from django_filters.rest_framework import FilterSet, ModelChoiceFilter
from django.db import models

from orders.models import Shift, Order, Product, OrderVenue
from venues.models import Venue


class ProductFilter(FilterSet):
    """Product FilterSet."""

    class Meta:
        """Meta class."""

        model = Product
        fields = {
            "available": ("exact",),
            "orderable": ("exact",),
            "ignore_shift_restrictions": ("exact",),
        }


class ShiftFilter(FilterSet):
    """Shift FilterSet."""

    venue = ModelChoiceFilter(field_name="venue__venue", to_field_name="slug", queryset=Venue.objects.all())

    class Meta:
        """Meta class."""

        model = Shift
        fields = {
            "start": ("lte", "gte"),
            "end": ("lte", "gte"),
            "can_order": ("exact",),
            "finalized": ("exact",),
            "assignees": ("exact",),
        }

    filter_overrides = {
        models.DateTimeField: {"filter_class": IsoDateTimeFilter},
    }


class OrderFilter(FilterSet):
    """Order FilterSet."""

    class Meta:
        """Meta class."""

        model = Order
        fields = {
            "user": (
                "exact",
                "isnull",
            ),
            "ready": ("exact",),
            "paid": ("exact",),
            "picked_up": ("exact",),
            "type": ("exact",),
            "product": ("exact",),
        }
