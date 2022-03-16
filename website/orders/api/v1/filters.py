from django_filters import IsoDateTimeFilter
from django_filters.rest_framework import FilterSet
from django.db import models

from orders.models import Shift, Order, Product


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

    class Meta:
        """Meta class."""

        model = Shift
        fields = {
            "start_date": ("lte", "gte"),
            "end_date": ("lte", "gte"),
            "venue": ("exact",),
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
            "type": ("exact",),
            "product": ("exact",),
        }
