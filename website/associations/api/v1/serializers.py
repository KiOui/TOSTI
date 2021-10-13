from rest_framework import serializers

from associations import models


class AssociationSerializer(serializers.ModelSerializer):
    """Association serializer."""

    class Meta:
        """Meta class."""

        model = models.Association
        fields = ["pk", "name"]
