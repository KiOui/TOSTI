from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin, messages
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
    list_filter = [ProductAdminVenueFilter, "available"]
    search_fields = ["name", "venue"]

    actions = ["make_available", "make_unavailable"]

    def make_available(self, request, queryset):
        messages.success(
            request,
            f"{queryset.filter(available=False).update(available=True)} products were marked as available",
        )
        return request

    make_available.short_description = "Make selected products available"

    def make_unavailable(self, request, queryset):
        messages.success(
            request,
            f"{queryset.filter(available=True).update(available=False)} products were marked as unavailable",
        )
        return request

    make_unavailable.short_description = "Make selected products unavailable"

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
        "capacity",
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

    readonly_fields = ["order_price", "paid_at", "delivered_at"]
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

    actions = ["set_paid", "set_delivered"]

    def set_paid(self, request, queryset):
        messages.success(
            request,
            f"{queryset.filter(paid=False).update(paid=True)} orders were marked as paid",
        )
        return request

    set_paid.short_description = "Mark selected orders as paid"

    def set_delivered(self, request, queryset):
        messages.success(
            request,
            f"{queryset.filter(delivered=False).update(delivered=True)} orders were marked as delivered",
        )
        return request

    set_delivered.short_description = "Mark selected orders as delivered"

    class Media:
        """Necessary to use AutocompleteFilter."""
