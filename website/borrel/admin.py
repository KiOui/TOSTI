from autocompletefilter.admin import AutocompleteFilterMixin
from autocompletefilter.filters import AutocompleteListFilter
from django.contrib import admin
from django.contrib.admin import EmptyFieldListFilter
from django.db import models
from django.forms import Textarea
from import_export.admin import ExportMixin, ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from .models import (
    BasicBorrelBrevet,
    BorrelReservation,
    Product,
    ProductCategory,
    ReservationItem,
)
from .resources import BasicBorrelBrevetResource, ProductResource, BorrelReservationResource


@admin.register(BasicBorrelBrevet)
class BasicBorrelBrevetAdmin(ExportMixin, admin.ModelAdmin):
    """Custom admin for basic borrel brevet."""

    resource_class = BasicBorrelBrevetResource
    list_display = ["user", "registered_on"]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__full_name",
        "user__override_display_name",
        "user__override_short_name",
    ]
    readonly_fields = ["registered_on"]
    autocomplete_fields = ["user"]


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


@admin.register(BorrelReservation)
class BorrelReservationAdmin(AutocompleteFilterMixin, ExportMixin, admin.ModelAdmin):
    """Custom admin for borrel reservations."""

    resource_class = BorrelReservationResource
    list_display = ["title", "association", "user_created", "start", "end", "accepted", "submitted"]
    search_fields = ["title"]
    autocomplete_fields = ["venue_reservation"]
    inlines = [ReservationItemInline]
    actions = ["accept_reservation", "reject_reservation"]

    def accept_reservation(self, request, queryset):
        """Accept reservations."""
        self._change_accepted(queryset, True)

    accept_reservation.short_description = "Accept selected reservations"

    def reject_reservation(self, request, queryset):
        """Reject reservations."""
        self._change_accepted(queryset, False)

    reject_reservation.short_description = "Reject selected reservations"

    @staticmethod
    def _change_accepted(queryset, status):
        queryset.update(accepted=status)
    
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
        ("user_created", AutocompleteListFilter),
        "accepted",
        ("submitted_at", EmptyFieldListFilter),
        "association",
        ("start", DateRangeFilter),
    )

    def get_queryset(self, request):
        """Return queryset."""
        return super().get_queryset(request).prefetch_related("association")

    def submitted(self, obj):
        """Reservation is submitted."""
        return obj.submitted if obj else None

    submitted.boolean = True
