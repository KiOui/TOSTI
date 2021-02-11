from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

User = get_user_model()


class UserRelatedField(serializers.ModelSerializer):
    """Serializers for Users."""

    username = serializers.CharField(source="__str__")

    class Meta:
        """Meta class."""

        model = User
        fields = [
            "id",
            "username",
        ]
        read_only_fields = ["id", "username"]


class UserSerializer(serializers.RelatedField):
    """User serializer."""

    def get_queryset(self):
        """Get queryset."""
        return User.objects.all()

    def to_representation(self, value):
        """Convert to string."""
        return value.__str__()

    def to_internal_value(self, data):
        """Convert a user to internal value."""
        if type(data) == int:
            return data
        raise ValidationError("Incorrect type. Expected pk value, received {}.".format(type(data)))
