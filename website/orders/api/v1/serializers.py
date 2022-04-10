from rest_framework import serializers

from orders import models
from orders.exceptions import OrderException
from orders.models import Order, Product
from orders.services import add_user_order, add_scanned_order
from users.api.v1.serializers import UserSerializer


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    # Swagger UI does not know a DecimalField so we have to do it this way
    current_price = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        """Convert a single integer (primary key) to a Product."""
        if type(data) == int:
            try:
                return Product.objects.get(id=data)
            except Product.DoesNotExist:
                raise serializers.ValidationError("Product with id {} not found.".format(data))
        else:
            return super(ProductSerializer, self).to_internal_value(data)

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
            "max_allowed_per_shift",
            "barcode",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""

    product = ProductSerializer(many=False, read_only=False)
    user = UserSerializer(many=False, read_only=True)

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
        try:
            if validated_data["type"] == Order.TYPE_ORDERED:
                return add_user_order(validated_data["product"], validated_data["shift"], validated_data["user"])
            else:
                return add_scanned_order(validated_data["product"], validated_data["shift"])
        except OrderException as e:
            raise serializers.ValidationError({"detail": e.__str__()})

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
        read_only_fields = ["id", "created", "user", "order_price", "ready_at", "paid_at"]


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift objects."""

    assignees = UserSerializer(many=True)
    amount_of_orders = serializers.SerializerMethodField()

    def get_amount_of_orders(self, instance):
        """Get the amount of orders in the shift."""
        return instance.orders.filter(type=Order.TYPE_ORDERED).count()

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
            return super().update(instance, validated_data)
        except ValueError as e:
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
        read_only_fields = ["id", "is_active", "finalized", "amount_of_orders"]
