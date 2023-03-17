from rest_framework import serializers

from tosti.api.serializers import WritableModelSerializer
from users.api.v1.serializers import UserSerializer
from venues import models
from associations.api.v1.serializers import AssociationSerializer
from rest_framework.exceptions import ValidationError as DRFValidationError


class VenueSerializer(serializers.ModelSerializer):
    """Venue serializer."""

    class Meta:
        """Meta class."""

        model = models.Venue
        fields = ["id", "name", "slug", "color_in_calendar", "can_be_reserved"]


class ReservationSerializer(WritableModelSerializer):
    """Reservation Serializer."""

    user_created = UserSerializer(many=False, read_only=True)
    venue = VenueSerializer(many=False, read_only=False)
    association = AssociationSerializer(many=False, read_only=False)

    def validate(self, attrs):
        """Make sure start is not after end."""
        start = attrs.get("start", None)
        end = attrs.get("end", None)

        if start is not None and end is not None and end <= start:
            raise DRFValidationError("Start can not be before end.")

        return attrs

    class Meta:
        """Meta class."""

        model = models.Reservation
        fields = [
            "id",
            "title",
            "created_at",
            "user_created",
            "association",
            "start",
            "end",
            "venue",
            "comments",
            "accepted",
        ]
        read_only_fields = [
            "id",
            "user_created",
            "created_at",
            "accepted",
        ]
