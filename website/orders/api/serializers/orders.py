from rest_framework import serializers
from orders import models


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Product
        fields = ['id', 'name', 'icon', 'available', 'available_at', 'current_price', 'orderable', 'ignore_shift_restrictions', 'max_allowed_per_shift', 'barcode']


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Order
        fields = ['id', 'created', 'user', 'shift', 'product', 'order_price', 'ready', 'ready_at', 'paid', 'paid_at', 'type']
        read_only_fields = ['pk', 'created', 'user', 'order_price', 'ready_at', 'paid_at']


class ShiftSerializer(serializers.ModelSerializer):

    def validate(self, data):
        if self.instance:
            start_date = data['start_date'] if 'start_date' in data.keys() else self.instance.start_date
            end_date = data['end_date'] if 'end_date' in data.keys() else self.instance.end_date
        else:
            if 'start_date' in data.keys():
                start_date = data['start_date']
            else:
                raise serializers.ValidationError("No start date specified")
            if 'end_date' in data.keys():
                end_date = data['end_date']
            else:
                raise serializers.ValidationError("No end date specified")

        if end_date <= start_date:
            raise serializers.ValidationError("End date cannot be before start date.")

        overlapping_start = (
            models.Shift.objects.filter(start_date__gte=start_date, start_date__lte=end_date, venue=self.instance.venue, )
            .exclude(pk=self.instance.pk)
            .count()
        )
        overlapping_end = (
            models.Shift.objects.filter(end_date__gte=start_date, end_date__lte=end_date, venue=self.instance.venue, )
            .exclude(pk=self.instance.pk)
            .count()
        )

        if overlapping_start > 0 or overlapping_end > 0:
            raise serializers.ValidationError("Overlapping shifts for the same venue are not allowed.")
        data = super().validate(data)
        return data

    class Meta:
        model = models.Shift
        fields = ['id', 'venue', 'start_date', 'end_date', 'can_order', 'max_orders_per_user', 'max_orders_total', 'assignees']
        read_only_fields = ['id', 'venue']
