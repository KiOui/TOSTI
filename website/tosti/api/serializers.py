from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ListSerializer
from rest_framework.utils import model_meta


class WritableModelSerializer(serializers.ModelSerializer):
    """
    ModelSerializer with writable model fields.

    When a field is added to this serializer that is actually a ModelSerializer by itself, the writable fields will
    be altered such that the ModelSerializers become writable by using their identification method (such as a primary
    key). Read-only ModelSerializers will not be altered.
    """

    def get_writable_fields(self):
        """Get writable fields."""
        return self._writable_fields

    @property
    def _writable_fields(self):
        """Alter the writable fields such that ModelSerializers become writable by using their id."""
        for field in self.fields.values():
            if not field.read_only:
                if isinstance(field, ModelSerializer):
                    model = getattr(self.Meta, "model")
                    info = model_meta.get_field_info(model)
                    relation_info = info.relations[field.field_name]
                    new_field_class, new_field_kwargs = self.build_relational_field(
                        field.field_name, relation_info
                    )
                    new_field = new_field_class(**new_field_kwargs)
                    new_field.bind(field_name=field.field_name, parent=self)
                    yield new_field
                elif isinstance(field, ListSerializer) and isinstance(
                    field.child, ModelSerializer
                ):
                    model = getattr(self.Meta, "model")
                    info = model_meta.get_field_info(model)
                    relation_info = info.relations[field.field_name]
                    new_field_class, new_field_kwargs = self.build_relational_field(
                        field.field_name, relation_info
                    )
                    new_field_kwargs["many"] = True
                    # We need to overwrite allow_empty because its default is different when creating a foreignkey
                    # field.
                    new_field_kwargs["allow_empty"] = field.allow_empty
                    new_field = new_field_class(**new_field_kwargs)
                    new_field.bind(field_name=field.field_name, parent=self)
                    yield new_field
                else:
                    yield field
