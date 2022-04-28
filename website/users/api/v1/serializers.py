from django.contrib.auth import get_user_model
from rest_framework import serializers

from associations.api.v1.serializers import AssociationSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializers for Users."""

    full_name = serializers.CharField(source="__str__")
    association = AssociationSerializer(source="profile.association")

    class Meta:
        """Meta class."""

        model = User
        fields = [
            "id",
            "full_name",
            "association",
        ]
        read_only_fields = ["id", "full_name", "association"]
