from django.contrib import admin
from django.contrib.admin import EmptyFieldListFilter
from django.db import models
from django.forms import Textarea
from import_export import resources
from import_export.admin import ExportMixin, ImportExportModelAdmin
from import_export.fields import Field

from .models import (
    BasicBorrelBrevet,
    BorrelReservation,
    Product,
    ProductCategory,
    ReservationItem,
)


class BasicBorrelBrevetResource(resources.ModelResource):
    """Basic Borrel Brevet Resource."""

    user__full_name = Field(attribute="user__full_name", column_name="full_name")
    user__first_name = Field(attribute="user__first_name", column_name="first_name")
    user__last_name = Field(attribute="user__last_name", column_name="last_name")
    user__username = Field(attribute="user__username", column_name="username")
    user__email = Field(attribute="user__email", column_name="email")

    class Meta:
        """Meta class."""

        model = BasicBorrelBrevet
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


@admin.register(BasicBorrelBrevet)
class BasicBorrelBrevetAdmin(ExportMixin, admin.ModelAdmin):
    """Custom admin for basic borrel brevet."""

    resource_class = BasicBorrelBrevetResource
    list_display = ["user", "registered_on"]
    search_fields = ["user"]
    readonly_fields = ["registered_on"]


class ProductResource(resources.ModelResource):
    """Product Resource."""

    category = Field(attribute="category", column_name="category")

    def before_import_row(self, row, row_number=None, **kwargs):
        """Create a new category when an import is being run with a non-existing category."""
        category_name = row.get("category", None)
        if category_name is None:
            return

        try:
            row["category"], _ = ProductCategory.objects.get_or_create(name=category_name)
        except ProductCategory.MultipleObjectsReturned:
            return

    class Meta:
        """Meta class."""

        model = Product
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


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    """Custom admin for borrel inventory products."""

    resource_class = ProductResource
    search_fields = ["name", "category"]
    list_display = [
        "name",
        "description",
        "price",
        "category",
        "active",
    ]
    list_filter = (
        "category",
        "active",
    )


@admin.register(ProductCategory)
class CategoryAdmin(ImportExportModelAdmin):
    """Custom admin for borrel inventory categories."""

    list_display = [
        "name",
    ]
    search_fields = ["name"]


class ReservationItemInline(admin.TabularInline):
    """Inline or reservation items."""

    model = ReservationItem
    fields = (
        "product",
        "product_name",
        "product_description",
        "amount_reserved",
        "amount_used",
    )
    readonly_fields = (
        "product_name",
        "product_description",
    )
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 1, "cols": 40})},
    }
    extra = 0
    ordering = (
        "product__category",
        "product__name",
    )


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
        product_names = ReservationItem.objects.filter(reservation__in=queryset).values_list("product_name", flat=True)
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
            reservation_item = ReservationItem.objects.get(
                reservation=obj, product_name=self.added_product_fields[field.attribute]
            )
            if field.attribute.endswith("_reserved"):
                return reservation_item.amount_reserved
            elif field.attribute.endswith("_used"):
                return reservation_item.amount_used
        except ReservationItem.DoesNotExist:
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

        model = BorrelReservation
        fields = [
            "title",
            "start",
            "end",
            "user_created__full_name",
            "user_updated__full_name",
            "user_submitted__full_name",
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
            "association__name",
            "comments",
            "accepted",
            "venue_reservation__venue__name",
        ]


@admin.register(BorrelReservation)
class BorrelReservationAdmin(ExportMixin, admin.ModelAdmin):
    """Custom admin for borrel reservations."""

    resource_class = BorrelReservationResource
    list_display = ["title", "association", "user_created", "start", "end", "accepted", "submitted"]
    search_fields = ["title", "user_created"]
    inlines = [ReservationItemInline]
    readonly_fields = (
        "created_at",
        "user_created",
        "updated_at",
        "user_updated",
        "submitted_at",
        "user_submitted",
        "join_code",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "start",
                    "end",
                    "association",
                    "venue_reservation",
                    "comments",
                    "accepted",
                )
            },
        ),
        (
            "Details",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "user_created",
                    "updated_at",
                    "user_updated",
                    "submitted_at",
                    "user_submitted",
                    "join_code",
                    "users_access",
                ),
            },
        ),
    )
    filter_horizontal = [
        "users_access",
    ]
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 4, "cols": 100})},
    }
    list_filter = (
        "accepted",
        ("submitted_at", EmptyFieldListFilter),
        "association",
        "start",
    )
    # date_hierarchy = "start"

    def submitted(self, obj):
        """Reservation is submitted."""
        return obj.submitted if obj else None

    submitted.boolean = True
