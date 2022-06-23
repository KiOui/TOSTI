from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializers for Users."""

    class Meta:
        """Meta class."""

        model = User
        fields = [
            "id",
            "name",
            "association",
        ]
        read_only_fields = ["id", "name", "association"]
