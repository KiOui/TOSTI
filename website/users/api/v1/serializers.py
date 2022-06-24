from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializers for Users."""
    display_name = serializers.CharField(source="__str__")

    class Meta:
        """Meta class."""

        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "display_name",
            "association",
        ]
        read_only_fields = ["id", "first_name", "last_name", "full_name", "display_name", "association"]
