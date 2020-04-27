from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from orders.models import Product, Order, Shift


class ProductAdminVenueFilter(AutocompleteFilter):
    """Filter class to filter product objects available at a certain venue."""

    title = "Venue"
    field_name = "available_at"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Custom admin for products."""

    list_display = ["name", "current_price", "available"]
    list_filter = [
        ProductAdminVenueFilter,
    ]
    search_fields = ["name", "venue"]

    class Media:
        """Necessary to use AutocompleteFilter."""


class ShiftAdminAssigneeFilter(AutocompleteFilter):
    """Filter class to filter shifts objects with certain assigned users."""

    title = "Assignee"
    field_name = "assignees"


@admin.register(Shift)
class ShiftAdmin(ImportExportModelAdmin):
    """Custom admin for products."""

    list_display = [
        "date",
        "start_time",
        "end_time",
        "venue",
        "number_of_orders",
        "orders_allowed",
        "can_order",
        "is_active",
    ]
    list_filter = [ShiftAdminAssigneeFilter, "venue", "orders_allowed"]

    search_fields = ["start_date", "venue"]

    class Media:
        """Necessary to use AutocompleteFilter."""


class OrderAdminUserFilter(AutocompleteFilter):
    """Filter class to filter Order objects on a certain user."""

    title = "User"
    field_name = "user"


class OrderAdminShiftFilter(AutocompleteFilter):
    """Filter class to filter Order objects on a certain shift."""

    title = "Shift"
    field_name = "shift"


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    """Custom admin for products."""

    readonly_fields = ["order_price"]
    list_display = ["user", "created", "get_venue", "product", "paid", "delivered"]
    list_filter = [
        OrderAdminUserFilter,
        OrderAdminShiftFilter,
        "product",
        "paid",
        "delivered",
        "shift__venue",
    ]
    search_fields = ["user", "shift"]

    class Media:
        """Necessary to use AutocompleteFilter."""
