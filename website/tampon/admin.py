from django.contrib import admin

from tampon.models import TamponNotification, Restock, Room, StockData, RestockItem


class RestockItemInline(admin.TabularInline):
    model = RestockItem
    extra = 0
    fields = ("stock_data", "quantity")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "active",
    )
    list_filter = ("active",)
    search_fields = (
        "name",
        "slug",
    )


@admin.register(TamponNotification)
class TamponNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "created_at",
        "is_resolved",
    )
    list_filter = ("room__name", "is_resolved", "created_at")
    search_fields = (
        "room__name",
        "comment",
    )


@admin.register(Restock)
class RestockAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "restock_time",
        "restocked_by",
    )
    list_filter = ("room__name", "restock_time")
    search_fields = (
        "room__name",
        "restocked_by__username",
    )
    inlines = [RestockItemInline]


@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ("name", "restock_default", "stock_amount")
    search_fields = ("name",)
