from django.contrib import admin
from django.db import models
from django.forms import Textarea

from .models import (
    BasicBorrelBrevet,
    BorrelReservation,
    BorrelInventoryProduct,
    BorrelInventoryCategory,
    ReservationItem,
)


@admin.register(BasicBorrelBrevet)
class BasicBorrelBrevetAdmin(admin.ModelAdmin):
    """Custom admin for basic borrel brevet."""

    list_display = ["user", "registered_on"]
    search_fields = ["user"]
    readonly_fields = ["registered_on"]


@admin.register(BorrelInventoryProduct)
class BorrelInventoryProductAdmin(admin.ModelAdmin):
    """Custom admin for borrel inventory products."""

    list_display = ["name", "active", "category"]
    search_fields = ["name", "category"]


@admin.register(BorrelInventoryCategory)
class BorrelInventoryCategoryAdmin(admin.ModelAdmin):
    """Custom admin for borrel inventory categories."""

    list_display = [
        "name",
    ]
    search_fields = ["name"]


class ReservationItemInline(admin.TabularInline):
    model = ReservationItem
    fields = ("product", "_price_per_unit", "amount_reserved", "_unit", "amount_used", "_unit2", "remarks")
    readonly_fields = (
        "_price_per_unit",
        "_unit",
        "_unit2",
    )
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 1, "cols": 40})},
    }

    def _price_per_unit(self, obj):
        return f"€ {obj.product_price_per_unit}" if obj and obj.product_price_per_unit else ""

    _price_per_unit.short_description = "Price per unit"

    def _unit(self, obj):
        return obj.product_unit_description if obj and obj.product_unit_description else ""

    _unit.short_description = ""

    def _unit2(self, obj):
        return self._unit(obj)

    _unit2.short_description = ""


@admin.register(BorrelReservation)
class ReservationRequestAdmin(admin.ModelAdmin):
    """Custom admin for Reservation requests."""

    list_display = ["title", "association", "user", "start", "end", "accepted", "submitted"]
    search_fields = ["title", "user"]
    inlines = [ReservationItemInline]
    readonly_fields = (
        "created_at",
        "updated_at",
        "submitted_at",
    )
    fields = (
        "title",
        "start",
        "end",
        "association",
        "venue_reservation",
        "comments",
        "user",
        "accepted",
        "created_at",
        "updated_at",
        "submitted_at",
    )
    formfield_overrides = {
        models.TextField: {"widget": Textarea(attrs={"rows": 4, "cols": 100})},
    }

    def submitted(self, obj):
        return obj.submitted if obj else None

    submitted.boolean = True
