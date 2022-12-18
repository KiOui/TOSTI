from rest_framework import serializers

from users.api.v1.serializers import UserSerializer
from venues import models
from associations.api.v1.serializers import AssociationSerializer


class VenueSerializer(serializers.ModelSerializer):
    """Venue serializer."""

    class Meta:
        """Meta class."""

        model = models.Venue
        fields = ["id", "name", "slug", "color_in_calendar", "can_be_reserved"]


class ReservationSerializer(serializers.ModelSerializer):
    """Reservation Serializer."""

    user_created = UserSerializer(many=False, read_only=True)
    venue = VenueSerializer(many=False, read_only=True)
    association = AssociationSerializer(many=False, read_only=True)

    class Meta:
        """Meta class."""

        model = models.Reservation
        fields = ["id", "title", "user_created", "association", "start", "end", "venue", "comments"]
