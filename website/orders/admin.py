from autocompletefilter.admin import AutocompleteFilterMixin
from autocompletefilter.filters import AutocompleteListFilter
from django import forms

from django.contrib import admin, messages
from django.contrib.admin import widgets
from django.db import models
from django.db.models import Q
from django.forms import CheckboxSelectMultiple
from django.urls import reverse
from guardian.admin import GuardedModelAdmin
from import_export.admin import ImportExportModelAdmin

from orders.models import Product, Order, Shift, OrderVenue, OrderBlacklistedUser

from users.models import User


@admin.register(OrderVenue)
class OrderVenueAdmin(GuardedModelAdmin):
    """Simple admin for OrderVenues."""

    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Custom admin for products."""

    list_display = ["name", "current_price", "available"]
    list_filter = ["available"]
    search_fields = ["name", "venue"]

    actions = ["make_available", "make_unavailable"]
    formfield_overrides = {
        models.ManyToManyField: {"widget": CheckboxSelectMultiple},
    }

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
    """Inline form for orders."""

    model = Order
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

        if "venue" in self.fields:
            self.fields["venue"].queryset = OrderVenue.objects.filter(venue__active=True)

        if "assignees" in self.fields:
            self.fields["assignees"].queryset = User.objects.all()

        if self.instance.pk:
            if "venue" in self.fields:
                self.fields["venue"].queryset = OrderVenue.objects.filter(
                    Q(venue__active=True) | Q(shifts=self.instance)
                ).distinct()
                self.fields["venue"].initial = OrderVenue.objects.filter(shifts=self.instance)
            if "assignees" in self.fields:
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

    list_display = [
        "date",
        "start_time",
        "end_time",
        "venue",
        "capacity",
        "get_is_active",
        "can_order",
        "finalized",
    ]

    list_filter = ["venue", "can_order", "finalized"]
    inlines = [OrderInline]

    search_fields = ["start", "venue__venue__name"]

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
    get_is_active.short_description = "active"

    def has_change_permission(self, request, obj=None):
        """Make shift read-only if the shift is finalized."""
        if obj and obj.finalized:
            return False
        return super().has_change_permission(request, obj)

    class Media:
        """Necessary to use AutocompleteFilter."""


class OrderAdminForm(forms.ModelForm):
    """Admin form to edit orders."""

    class Meta:
        """Meta class for OrderAdminForm."""

        model = Order
        exclude = []

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        if "product" in self.fields:
            self.fields["product"].queryset = Product.objects.filter(available=True)

        if "shift" in self.fields:
            self.fields["shift"].queryset = Shift.objects.filter(can_order=True)

        if self.instance.pk:
            if "product" in self.fields:
                self.fields["product"].queryset = Product.objects.filter(
                    Q(available=True) | Q(pk=self.instance.product.pk)
                ).distinct()
                self.fields["product"].initial = self.instance.product
            if "shift" in self.fields:
                self.fields["shift"].queryset = Shift.objects.filter(
                    Q(can_order=True) | Q(pk=self.instance.shift.pk)
                ).distinct()
                self.fields["shift"].initial = self.instance.shift


@admin.register(Order)
class OrderAdmin(AutocompleteFilterMixin, ImportExportModelAdmin):
    """Custom admin for orders."""

    form = OrderAdminForm

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
        ("shift", AutocompleteListFilter),
        "product",
        "ready",
        "paid",
        "shift__venue",
    ]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__full_name",
        "user__email",
        "user__username",
        "user_association__name",
    ]

    actions = ["set_ready", "set_paid"]

    def has_change_permission(self, request, obj=None):
        """Make order read-only if the shift is finalized."""
        if obj and obj.shift.finalized:
            return False
        return super().has_change_permission(request, obj)

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

    def get_venue(self, obj):
        """Venue of the order."""
        return obj.shift.venue

    get_venue.short_description = "venue"
    get_venue.admin_order_field = "shift__venue"

    class Media:
        """Necessary to use AutocompleteFilter."""


@admin.register(OrderBlacklistedUser)
class OrderBlacklistedUserAdmin(admin.ModelAdmin):
    """Admin for blacklisted users."""

    autocomplete_fields = ["user"]
