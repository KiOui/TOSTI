from django_filters.rest_framework import FilterSet
from thaliedje.models import Player


class PlayerFilter(FilterSet):
    """Player FilterSet."""

    class Meta:
        """Meta class."""

        model = Player
        fields = {
            "venue": ("exact",),
        }
