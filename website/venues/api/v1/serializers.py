from rest_framework import serializers

from django.utils import timezone
from django.db.models import Q

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

    def validate_start(self, value):
        now = timezone.now()
        if value <= now:
            raise DRFValidationError("Reservation should be in the future")
        return value

    def validate(self, attrs):
        """Make sure start is not after end."""
        start = attrs.get("start")
        end = attrs.get("end")

        if end <= start:
            raise DRFValidationError("Start can not be before end.")

        venue = attrs.get("venue")
        if not venue.can_be_reserved:
            raise DRFValidationError(f"Venue {venue} is not reservable")

        if (
            models.Reservation.objects.filter(venue=venue)
            .filter(accepted=True)
            .filter(
                Q(start__lte=start, end__gt=start)
                | Q(start__lt=end, end__gte=end)
                | Q(start__gte=start, end__lte=end)
            )
            .exists()
        ):
            raise DRFValidationError(
                "An overlapping reservation for this venue already exists."
            )

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
