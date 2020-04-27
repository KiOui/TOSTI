from admin_auto_filters.filters import AutocompleteFilter
from django import forms

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from orders.models import Product, Order, Shift
from venues.models import Venue


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Custom admin for products."""


class OrderAdminAssigneeFilter(AutocompleteFilter):
    """Filter class to filter Client objects."""

    title = "Assignee"
    field_name = "assignees"


@admin.register(Shift)
class ShiftAdmin(ImportExportModelAdmin):
    """Custom admin for products."""

    list_display = [
        "get_date_formatted",
        "venue",
        "number_of_orders",
        "orders_allowed",
        "can_order",
        "is_active",
    ]
    list_filter = [OrderAdminAssigneeFilter, "venue", "orders_allowed"]

    class Media:
        """Necessary to use AutocompleteFilter."""


class OrderAdminUserFilter(AutocompleteFilter):
    """Filter class to filter Client objects."""

    title = "User"
    field_name = "user"


class OrderAdminShiftFilter(AutocompleteFilter):
    """Filter class to filter Client objects."""

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
        "paid",
        "delivered",
        "product",
    ]
    search_fields = ["user", "shift"]

    class Media:
        """Necessary to use AutocompleteFilter."""
