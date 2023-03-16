import traceback

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.utils import model_meta

from orders import models
from orders.models import Order, Product, OrderVenue
from orders.services import add_user_order, add_scanned_order
from tosti.api.serializers import WritableModelSerializer
from users.api.v1.serializers import UserSerializer
from venues.api.v1.serializers import VenueSerializer


class OrderVenueSerializer(serializers.ModelSerializer):
    """Order Venue Serializer."""

    venue = VenueSerializer(many=False, read_only=True)

    class Meta:
        """Meta class."""

        model = OrderVenue
        fields = ["venue"]
        read_only_fields = ["venue"]


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    def to_internal_value(self, data):
        """Convert a single integer (primary key) to a Product."""
        if type(data) == int:
            try:
                return Product.objects.get(id=data)
            except Product.DoesNotExist:
                raise serializers.ValidationError("Product with id {} not found.".format(data))
        else:
            return super(ProductSerializer, self).to_internal_value(data)

    class Meta:
        """Meta class."""

        model = models.Product
        fields = [
            "id",
            "name",
            "icon",
            "available",
            "current_price",
            "orderable",
            "ignore_shift_restrictions",
            "max_allowed_per_shift",
            "barcode",
        ]

        read_only_fields = ["current_price"]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""

    product = ProductSerializer(many=False, read_only=False)
    user = UserSerializer(many=False, read_only=True)

    def __init__(self, *args, **kwargs):
        """Override readonly of some fields."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            # If we are updating.
            self.fields.get("type").read_only = True
            self.fields.get("product").read_only = True

    def validate_product(self, value):
        """Validate the product id."""
        shift = self.context.get("shift", None)
        if shift:
            if Product.objects.filter(available_at=shift.venue, id=value.id).exists():
                return value
            else:
                raise serializers.ValidationError(
                    "Product {} is not available in venue {}.".format(value, shift.venue)
                )
        else:
            return value

    def create(self, validated_data):
        """
        Create an Order from validated serialized data.

        This function uses add_order to add an Order to a Shift
        :param validated_data: validated serialized data
        :return: an Order if the Order could be successfully added, a ValidationError otherwise
        """
        if validated_data.get("type", Order.TYPE_ORDERED) == Order.TYPE_ORDERED:
            return add_user_order(**validated_data)
        else:
            return add_scanned_order(validated_data["product"], validated_data["shift"])

    class Meta:
        """Meta class."""

        model = models.Order
        fields = [
            "id",
            "created",
            "user",
            "product",
            "order_price",
            "ready",
            "ready_at",
            "paid",
            "paid_at",
            "type",
            "prioritize",
            "deprioritize",
        ]
        read_only_fields = ["id", "created", "user", "product", "order_price", "ready_at", "paid_at", "prioritize"]


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift objects."""

    assignees = WritableModelSerializer(serializer=UserSerializer, many=True, read_only=False)
    amount_of_orders = serializers.SerializerMethodField()
    venue = WritableModelSerializer(serializer=OrderVenueSerializer, many=False, read_only=False)

    def __init__(self, *args, **kwargs):
        """Override readonly of some fields."""
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            # If we are updating.
            self.fields.get("venue").read_only = True

    def get_amount_of_orders(self, instance):
        """Get the amount of orders in the shift."""
        return instance.orders.filter(type=Order.TYPE_ORDERED).count()

    def create(self, validated_data):
        """
        Create a Shift.

        Catch any ValidationError exception that may be caused by the save() method of the Shift object.
        """
        try:
            ModelClass = self.Meta.model

            # Remove many-to-many relationships from validated_data.
            # They are not valid arguments to the default `.create()` method,
            # as they require that the instance has already been saved.
            info = model_meta.get_field_info(ModelClass)
            many_to_many = {}
            for field_name, relation_info in info.relations.items():
                if relation_info.to_many and (field_name in validated_data):
                    many_to_many[field_name] = validated_data.pop(field_name)

            try:
                instance = ModelClass._default_manager.create(**validated_data)
            except TypeError:
                tb = traceback.format_exc()
                msg = (
                        'Got a `TypeError` when calling `%s.%s.create()`. '
                        'This may be because you have a writable field on the '
                        'serializer class that is not a valid argument to '
                        '`%s.%s.create()`. You may need to make the field '
                        'read-only, or override the %s.create() method to handle '
                        'this correctly.\nOriginal exception was:\n %s' %
                        (
                            ModelClass.__name__,
                            ModelClass._default_manager.name,
                            ModelClass.__name__,
                            ModelClass._default_manager.name,
                            self.__class__.__name__,
                            tb
                        )
                )
                raise TypeError(msg)

            # Save many-to-many relationships after the instance is created.
            if many_to_many:
                for field_name, value in many_to_many.items():
                    field = getattr(instance, field_name)
                    field.set(value)

            return instance
        except ValidationError as e:
            raise serializers.ValidationError(e)

    def update(self, instance, validated_data):
        """
        Update a Shift.

        Catch any ValidationError exception that may be caused by the save() method of the Shift object.
        """
        try:
            info = model_meta.get_field_info(instance)

            # Simply set each attribute on the instance, and then save it.
            # Note that unlike `.create()` we don't need to treat many-to-many
            # relationships as being a special case. During updates we already
            # have an instance pk for the relationships to be associated with.
            m2m_fields = []
            for attr, value in validated_data.items():
                if attr in info.relations and info.relations[attr].to_many:
                    m2m_fields.append((attr, value))
                else:
                    setattr(instance, attr, value)

            instance.save()

            # Note that many-to-many fields are set after updating instance.
            # Setting m2m fields triggers signals which could potentially change
            # updated instance and we do not want it to collide with .update()
            for attr, value in m2m_fields:
                field = getattr(instance, attr)
                field.set(value)

            return instance
        except ValidationError as e:
            raise serializers.ValidationError(e)

    class Meta:
        """Meta class."""

        model = models.Shift
        fields = [
            "id",
            "venue",
            "start",
            "end",
            "can_order",
            "is_active",
            "finalized",
            "amount_of_orders",
            "max_orders_per_user",
            "max_orders_total",
            "assignees",
        ]
        read_only_fields = ["id", "is_active", "amount_of_orders"]
