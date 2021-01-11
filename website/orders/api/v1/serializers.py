from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from orders import models
from orders.exceptions import OrderException
from orders.services import add_order
from django.contrib.auth import get_user_model

User = get_user_model()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    max_allowed = serializers.SerializerMethodField()

    def get_max_allowed(self, instance):
        """Get the maximum amount of orders a user can still place for this product."""
        return instance.user_max_order_amount(self.context["request"].user, self.context["request"].data.get("shift"))

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
            "max_allowed",
            "max_allowed_per_shift",
            "barcode",
        ]


class ProductAbbrSerializer(serializers.ModelSerializer):
    """Serializer for Product name only."""

    class Meta:
        """Meta class."""

        model = models.Product
        fields = [
            "name",
            "icon",
        ]
        read_only_fields = ["name", "icon"]


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


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creation of Order."""

    def create(self, validated_data):
        """
        Create an Order from validated serialized data.

        This function uses add_order to add an Order to a Shift
        :param validated_data: validated serialized data
        :return: an Order if the Order could be successfully added, a ValidationError otherwise
        """
        try:
            return add_order(
                validated_data["product"],
                validated_data["shift"],
                validated_data["type"],
                user=validated_data["user"],
                paid=validated_data["paid"],
                ready=validated_data["ready"],
                force=False,
                dry=False,
            )
        except OrderException as e:
            raise serializers.ValidationError(e.__str__())

    class Meta:
        """Meta class."""

        model = models.Order
        fields = [
            "user",
            "product",
            "ready",
            "paid",
            "type",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""

    product = ProductAbbrSerializer(many=False, read_only=True)
    user = UserRelatedField(many=False, read_only=True)

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
        ]
        read_only_fields = ["id", "created", "user", "product", "order_price", "ready_at", "paid_at", "type"]


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


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift objects."""

    assignees = UserSerializer(many=True)
    amount_of_orders = serializers.SerializerMethodField()
    max_user_orders = serializers.SerializerMethodField()

    def get_amount_of_orders(self, instance):
        """Get the amount of orders in the shift."""
        return instance.number_of_orders

    def get_max_user_orders(self, instance):
        """Get the max orders a user can still place in the shift."""
        return instance.user_max_order_amount(self.context["request"].user)

    def validate(self, data):
        """
        Validate serialized data.

        :param data: serialized data
        :return: the serialized data or a ValidationError if the Shift has a wrong start or end date
        """
        if self.instance:
            start_date = data["start_date"] if "start_date" in data.keys() else self.instance.start_date
            end_date = data["end_date"] if "end_date" in data.keys() else self.instance.end_date
            venue = data["venue"] if "venue" in data.keys() else self.instance.venue
        else:
            start_date = data["start_date"]
            end_date = data["end_date"]
            venue = data["venue"]

        if end_date <= start_date:
            raise serializers.ValidationError("End date cannot be before start date.")

        if self.instance:
            overlapping_start = (
                models.Shift.objects.filter(start_date__gte=start_date, start_date__lte=end_date, venue=venue,)
                .exclude(pk=self.instance.pk)
                .count()
            )
            overlapping_end = (
                models.Shift.objects.filter(end_date__gte=start_date, end_date__lte=end_date, venue=venue,)
                .exclude(pk=self.instance.pk)
                .count()
            )
        else:
            overlapping_start = models.Shift.objects.filter(
                start_date__gte=start_date, start_date__lte=end_date, venue=venue,
            ).count()
            overlapping_end = models.Shift.objects.filter(
                end_date__gte=start_date, end_date__lte=end_date, venue=venue,
            ).count()

        if overlapping_start > 0 or overlapping_end > 0:
            raise serializers.ValidationError("Overlapping shifts for the same venue are not allowed.")
        data = super().validate(data)
        return data

    class Meta:
        """Meta class."""

        model = models.Shift
        fields = [
            "id",
            "venue",
            "start_date",
            "end_date",
            "can_order",
            "amount_of_orders",
            "max_orders_per_user",
            "max_orders_total",
            "max_user_orders",
            "assignees",
        ]
        read_only_fields = ["id", "amount_of_orders", "max_user_orders"]
