from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ListSerializer
from rest_framework.utils import model_meta


class WritableModelSerializer(serializers.Serializer):
    """
    ModelSerializer with writable model fields.

    When a field is added to this serializer that is actually a ModelSerializer by itself, the writable fields will
    be altered such that the ModelSerializers become writable by using their identification method (such as a primary
    key). Read-only ModelSerializers will not be altered.
    """

    def __init__(self, serializer, *args, **kwargs):
        many = kwargs.pop('many', False)
        read_only = kwargs.pop('read_only', False)
        write_only = kwargs.pop('write_only', False)
        if read_only:
            raise ValueError()
        if write_only:
            raise ValueError()

        if not issubclass(serializer, serializers.ModelSerializer):
            raise Exception()

        self.read_serializer = serializer(many=many, read_only=True, write_only=False, *args, **kwargs)
        self.write_serializer = serializers.ModelSerializer.serializer_related_field(queryset=self.read_serializer.Meta.model.objects.all(), many=many, read_only=False, write_only=True, *args, **kwargs)

        # serializer(many=many, read_only=False, write_only=True, *args, **kwargs)

        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        return self.write_serializer.to_internal_value(data)

    def to_representation(self, instance):
        return self.read_serializer.to_representation(instance)
