from import_export.fields import Field
from import_export import resources
from borrel import models


class BasicBorrelBrevetResource(resources.ModelResource):
    """Basic Borrel Brevet Resource."""

    user__full_name = Field(attribute="user__full_name", column_name="full_name")
    user__first_name = Field(attribute="user__first_name", column_name="first_name")
    user__last_name = Field(attribute="user__last_name", column_name="last_name")
    user__username = Field(attribute="user__username", column_name="username")
    user__email = Field(attribute="user__email", column_name="email")

    class Meta:
        """Meta class."""

        model = models.BasicBorrelBrevet
        fields = [
            "user__full_name",
            "user__first_name",
            "user__last_name",
            "user__username",
            "user__email",
            "registered_on",
        ]
        export_order = [
            "user__full_name",
            "user__first_name",
            "user__last_name",
            "user__username",
            "user__email",
            "registered_on",
        ]


class ProductResource(resources.ModelResource):
    """Product Resource."""

    category = Field(attribute="category", column_name="category")

    def before_import_row(self, row, row_number=None, **kwargs):
        """Create a new category when an import is being run with a non-existing category."""
        category_name = row.get("category", None)
        if category_name is None:
            return

        try:
            row["category"], _ = models.ProductCategory.objects.get_or_create(name=category_name)
        except models.ProductCategory.MultipleObjectsReturned:
            return

    class Meta:
        """Meta class."""

        model = models.Product
        fields = [
            "id",
            "name",
            "active",
            "price",
            "category",
            "description",
        ]
        export_order = [
            "id",
            "name",
            "active",
            "price",
            "category",
            "description",
        ]


class BorrelReservationResource(resources.ModelResource):
    """Borrel Reservation Resource."""

    user_created__full_name = Field(attribute="user_created__full_name", column_name="user_created")
    user_updated__full_name = Field(attribute="user_updated__full_name", column_name="user_updated")
    user_submitted__full_name = Field(attribute="user_submitted__full_name", column_name="user_submitted")
    venue_reservation__venue__name = Field(attribute="venue_reservation__venue__name", column_name="venue")
    association__name = Field(attribute="association__name", column_name="association")

    def __init__(self):
        """Initialize by creating a field for each product."""
        super(BorrelReservationResource, self).__init__()
        self.added_product_fields = dict()

    def before_export(self, queryset, *args, **kwargs):
        """Initialize by creating a field for each product."""
        product_names = models.ReservationItem.objects.filter(reservation__in=queryset).values_list(
            "product_name", flat=True
        )
        for product_name in product_names:
            attribute_id_reserved = f"__product_{product_name}_reserved"
            attribute_id_used = f"__product_{product_name}_used"
            self.fields[attribute_id_reserved] = Field(
                column_name=f"{product_name} (reserved)", attribute=attribute_id_reserved, readonly=True
            )
            self.added_product_fields[attribute_id_reserved] = product_name
            self.fields[attribute_id_used] = Field(
                column_name=f"{product_name} (used)", attribute=attribute_id_used, readonly=True
            )
            self.added_product_fields[attribute_id_used] = product_name

    def export_product_field(self, field, obj):
        """Export the custom product fields."""
        try:
            reservation_item = models.ReservationItem.objects.get(
                reservation=obj, product_name=self.added_product_fields[field.attribute]
            )
            if field.attribute.endswith("_reserved"):
                return reservation_item.amount_reserved
            elif field.attribute.endswith("_used"):
                return reservation_item.amount_used
        except models.ReservationItem.DoesNotExist:
            pass
        return None

    def export_field(self, field, obj):
        """Check for added product field before exporting."""
        if field.attribute in self.added_product_fields.keys():
            return self.export_product_field(field, obj)
        else:
            return super(BorrelReservationResource, self).export_field(field, obj)

    class Meta:
        """Meta class."""

        model = models.BorrelReservation
        fields = [
            "title",
            "start",
            "end",
            "user_created__full_name",
            "user_updated__full_name",
            "user_submitted__full_name",
            "created_at",
            "updated_at",
            "submitted_at",
            "association__name",
            "comments",
            "accepted",
            "venue_reservation__venue__name",
        ]
        export_order = [
            "title",
            "start",
            "end",
            "user_created__full_name",
            "user_updated__full_name",
            "user_submitted__full_name",
            "created_at",
            "updated_at",
            "submitted_at",
            "association__name",
            "comments",
            "accepted",
            "venue_reservation__venue__name",
        ]
