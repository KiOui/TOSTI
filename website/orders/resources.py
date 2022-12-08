from import_export import resources
from import_export.fields import Field

from orders import models


class ShiftResource(resources.ModelResource):
    """Shift Resource."""

    def __init__(self):
        """Initialize by creating a field for each product."""
        super(ShiftResource, self).__init__()
        self.added_product_fields = dict()

    def before_export(self, queryset, *args, **kwargs):
        """Initialize by creating a field for each product."""
        product_names = models.Order.objects.filter(shift__in=queryset).values_list("product__name", "product__id")
        for product_name, product_id in product_names:
            attribute_id_ordered = f"__product_{product_name}_ordered"
            self.fields[attribute_id_ordered] = Field(
                column_name=f"{product_name}", attribute=attribute_id_ordered, readonly=True
            )
            self.added_product_fields[attribute_id_ordered] = product_id

    def export_product_field(self, field, obj):
        """Export the custom product fields."""
        try:
            amount_of_orders = models.Order.objects.filter(
                shift=obj, product_id=self.added_product_fields[field.attribute]
            ).count()
            return amount_of_orders
        except models.Order.DoesNotExist:
            pass
        return None

    def export_field(self, field, obj):
        """Check for added product field before exporting."""
        if field.attribute in self.added_product_fields.keys():
            return self.export_product_field(field, obj)
        else:
            return super(ShiftResource, self).export_field(field, obj)

    class Meta:
        """Meta class."""

        model = models.Shift
        fields = [
            "id",
            "venue",
            "start",
            "end",
            "can_order",
            "finalized",
            "max_orders_per_user",
            "max_orders_total",
            "assignees",
        ]
        export_order = [
            "id",
            "venue",
            "start",
            "end",
            "can_order",
            "finalized",
            "max_orders_per_user",
            "max_orders_total",
            "assignees",
        ]
