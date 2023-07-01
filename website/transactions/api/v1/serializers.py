from rest_framework import serializers

from transactions import models
from users.api.v1.serializers import UserSerializer


class AccountSerializer(serializers.ModelSerializer):
    """Account serializer."""

    user = UserSerializer(many=False)

    class Meta:
        """Meta class."""

        model = models.Account
        fields = ["user", "created_at", "balance"]
