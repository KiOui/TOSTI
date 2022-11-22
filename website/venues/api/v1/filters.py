from django_filters import BooleanFilter, IsoDateTimeFilter
from django_filters.rest_framework import FilterSet
from django.db import models

from venues.models import Reservation, Venue


class VenueFilter(FilterSet):
    """Venue FilterSet."""

    is_ordervenue = BooleanFilter(
        field_name="ordervenue",
        lookup_expr="isnull",
        exclude=True,
        label="Is OrderVenue",
    )

    class Meta:
        """Meta class."""

        model = Venue
        fields = {
            "can_be_reserved": ("exact",),
        }


class ReservationFilter(FilterSet):
    """Reservation FilterSet."""

    class Meta:
        """Meta class."""

        model = Reservation
        fields = {
            "user": ("exact",),
            "venue": ("exact",),
            "association": ("exact", "isnull"),
            "start": ("lte", "gte"),
            "end": ("lte", "gte"),
        }

    filter_overrides = {
        models.DateTimeField: {"filter_class": IsoDateTimeFilter},
    }
