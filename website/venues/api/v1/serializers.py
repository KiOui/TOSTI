from rest_framework import serializers

from users.api.v1.serializers import UserRelatedField
from venues import models
from associations.api.v1.serializers import AssociationSerializer


class VenueSerializer(serializers.ModelSerializer):
    """Venue serializer."""

    class Meta:
        """Meta class."""

        model = models.Venue
        fields = ["pk", "name", "color_in_calendar", "can_be_reserved"]


class ReservationSerializer(serializers.ModelSerializer):
    """Reservation Serializer."""

    user = UserRelatedField(many=False, read_only=True)
    venue = VenueSerializer(many=False, read_only=True)
    association = AssociationSerializer(many=False, read_only=True)

    class Meta:
        """Meta class."""

        model = models.Reservation
        fields = ["pk", "title", "user", "association", "start_time", "end_time", "venue", "comment"]
