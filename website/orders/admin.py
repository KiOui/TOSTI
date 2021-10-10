from admin_auto_filters.filters import AutocompleteFilter
from django import forms

from django.contrib import admin, messages
from django.contrib.admin import widgets
from django.db.models import Q
from django.urls import reverse
from guardian.admin import GuardedModelAdmin
from import_export.admin import ImportExportModelAdmin

from orders.models import Product, Order, Shift, OrderVenue

from users.models import User


@admin.register(OrderVenue)
class OrderVenueAdmin(GuardedModelAdmin):
    """Simple admin for OrderVenues."""

    pass


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

    def clean_barcode(self):
        """Clean barcode."""
        if self.cleaned_data["barcode"] == "" or self.cleaned_data["barcode"] is None:
            return None
        else:
            return self.cleaned_data["barcode"]

    def make_available(self, request, queryset):
        """
        Make a QuerySet of products available.

        :param request: the request
        :param queryset: the queryset of products
        :return: the request
        """
        messages.success(
            request,
            f"{queryset.filter(available=False).update(available=True)} products were marked as available",
        )
        return request

    make_available.short_description = "Make selected products available"

    def make_unavailable(self, request, queryset):
        """
        Make a QuerySet of product unavailable.

        :param request: the request
        :param queryset: the queryset of products
        :return: the request
        """
        messages.success(
            request,
            f"{queryset.filter(available=True).update(available=False)} products were marked as unavailable",
        )
        return request

    make_unavailable.short_description = "Make selected products unavailable"

    class Media:
        """Necessary to use AutocompleteFilter."""


class OrderInline(admin.TabularInline):
    """Inline form for Registration."""

    model = Order
    readonly_fields = [
        "user",
        "product",
        "order_price",
        "created",
        "paid_at",
        "ready_at",
    ]
    extra = 0


class ShiftAdminForm(forms.ModelForm):
    """Admin form to edit shifts."""

    class Meta:
        """Meta class for ShiftAdminForm."""

        model = Shift
        exclude = []

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        self.fields["venue"].queryset = OrderVenue.objects.filter(venue__active=True)
        self.fields["assignees"].queryset = User.objects.all()

        if self.instance.pk:
            self.fields["venue"].queryset = OrderVenue.objects.filter(
                Q(venue__active=True) | Q(shift=self.instance)
            ).distinct()
            self.fields["venue"].initial = OrderVenue.objects.filter(shift=self.instance)
            self.fields["assignees"].initial = User.objects.filter(shift=self.instance)

    assignees = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=widgets.FilteredSelectMultiple("Assignees", False),
    )


@admin.register(Shift)
class ShiftAdmin(GuardedModelAdmin, ImportExportModelAdmin):
    """Custom admin for shifts."""

    form = ShiftAdminForm
    date_hierarchy = "start_date"

    list_display = [
        "date",
        "start_time",
        "end_time",
        "venue",
        "capacity",
        "get_is_active",
        "can_order",
    ]

    list_filter = ["venue", "can_order"]
    inlines = [OrderInline]

    search_fields = ["start_date", "venue__venue__name"]

    actions = ["close_shift"]

    def view_on_site(self, obj):
        """
        Get the URL for the frontend view of this shift.

        :param obj: the shift object
        :return: the url to the frontend view of the shift
        """
        return reverse("orders:shift_admin", kwargs={"shift": obj})

    def close_shift(self, request, queryset):
        """
        Close a QuerySet of shifts.

        :param request: the request
        :param queryset: a queryset of shifts
        :return: the request
        """
        messages.success(
            request,
            f"{queryset.filter(can_order=True).update(can_order=False)} shifts were closed",
        )
        return request

    close_shift.short_description = "Close orders for shift"

    def get_is_active(self, obj):
        """Property for whether a shift is currently active."""
        return obj.is_active

    get_is_active.boolean = True

    class Media:
        """Necessary to use AutocompleteFilter."""


class OrderAdminShiftFilter(AutocompleteFilter):
    """Filter class to filter Order objects on a certain shift."""

    title = "Shift"
    field_name = "shift"


class OrderAdminForm(forms.ModelForm):
    """Admin form to edit orders."""

    class Meta:
        """Meta class for OrderAdminForm."""

        model = Order
        exclude = []

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        self.fields["product"].queryset = Product.objects.filter(available=True)
        self.fields["shift"].queryset = Shift.objects.filter(can_order=True)

        if self.instance.pk:
            self.fields["product"].queryset = Product.objects.filter(
                Q(available=True) | Q(order=self.instance)
            ).distinct()
            self.fields["product"].initial = Product.objects.filter(order=self.instance)
            self.fields["shift"].queryset = Shift.objects.filter(Q(can_order=True) | Q(order=self.instance)).distinct()
            self.fields["shift"].initial = Shift.objects.filter(order=self.instance)


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    """Custom admin for orders."""

    form = OrderAdminForm

    date_hierarchy = "created"

    readonly_fields = ["order_price", "created", "ready_at", "paid_at"]
    list_display = [
        "user",
        "created",
        "get_venue",
        "product",
        "ready",
        "paid",
    ]
    list_filter = [
        OrderAdminShiftFilter,
        "product",
        "ready",
        "paid",
        "shift__venue",
    ]
    search_fields = ["user", "shift"]

    actions = ["set_ready", "set_paid"]

    def set_ready(self, request, queryset):
        """
        Set orders in a QuerySet as ready.

        :param request: the request
        :param queryset: a queryset of orders
        :return: the request
        """
        messages.success(
            request,
            f"{queryset.filter(ready=False).update(ready=True)} orders were marked as ready",
        )
        return request

    set_ready.short_description = "Mark selected orders as ready"

    def set_paid(self, request, queryset):
        """
        Set orders in a QuerySet as paid.

        :param request: the request
        :param queryset: a queryset of orders
        :return: the request
        """
        messages.success(
            request,
            f"{queryset.filter(paid=False).update(paid=True)} orders were marked as paid",
        )
        return request

    set_paid.short_description = "Mark selected orders as paid"

    class Media:
        """Necessary to use AutocompleteFilter."""
