from rest_framework import serializers

from users.api.v1.serializers import UserRelatedField
from venues import models


class VenueSerializer(serializers.ModelSerializer):
    """Venue serializer."""

    class Meta:
        """Meta class."""

        model = models.Venue
        fields = ["pk", "name", "color_in_calendar"]


class ReservationSerializer(serializers.ModelSerializer):
    """Reservation Serializer."""

    user = UserRelatedField(many=False, read_only=True)
    venue = VenueSerializer(many=False, read_only=True)

    class Meta:
        """Meta class."""

        model = models.Reservation
        fields = ["pk", "name", "user", "start_time", "end_time", "venue"]
