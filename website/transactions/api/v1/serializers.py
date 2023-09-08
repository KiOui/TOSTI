from rest_framework import serializers

from transactions import models
from users.api.v1.serializers import UserSerializer

from tosti.api.serializers import WritableModelSerializer


class AccountSerializer(serializers.ModelSerializer):
    """Account serializer."""

    user = UserSerializer(many=False)

    class Meta:
        """Meta class."""

        model = models.Account
        fields = ["id", "user", "created_at", "balance"]


class TransactionSerializer(WritableModelSerializer):
    """Transaction Serializer."""

    account = AccountSerializer(many=False, read_only=False)

    class Meta:
        """Meta class."""

        model = models.Transaction
        fields = [
            "id",
            "account",
            "amount",
            "timestamp",
            "description",
            "processor",
        ]
        read_only_fields = (
            "id",
            "timestamp",
            "processor",
        )
