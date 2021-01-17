from rest_framework import serializers

from orders import models
from orders.exceptions import OrderException
from orders.models import Order
from orders.services import add_order
from users.api.v1.serializers import UserRelatedField, UserSerializer


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    max_allowed = serializers.SerializerMethodField()
    # Swagger UI does not know a DecimalField so we have to do it this way
    current_price = serializers.SerializerMethodField()

    def get_max_allowed(self, instance):
        """Get the maximum amount of orders a user can still place for this product."""
        return instance.user_max_order_amount(self.context["request"].user, self.context["request"].data.get("shift"))

    def get_current_price(self, instance):
        """Get the current price."""
        return instance.current_price

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
                paid=validated_data["type"] == Order.TYPE_SCANNED,
                ready=validated_data["type"] == Order.TYPE_SCANNED,
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

    def create(self, validated_data):
        """
        Create a Shift.

        Catch any ValueError exception that may be caused by the save() method of the Shift object.
        """
        try:
            super().create(validated_data)
        except ValueError as e:
            raise serializers.ValidationError(e)

    def update(self, instance, validated_data):
        """
        Update a Shift.

        Catch any ValueError exception that may be caused by the save() method of the Shift object.
        """
        try:
            super().update(instance, validated_data)
        except ValueError as e:
            raise serializers.ValidationError(e)

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
