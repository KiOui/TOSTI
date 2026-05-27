from django.contrib import admin

from tampon.models import TamponNotification, Restock, Room, StockData, RestockItem


class RestockItemInline(admin.TabularInline):
    model = RestockItem
    extra = 0
    fields = ("stock_data", "quantity")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "building",
        "floor_number",
        "room_number",
        "active",
    )
    list_filter = (
        "building",
        "floor_number",
        "active",
    )
    search_fields = (
        "building",
        "room_number",
    )


@admin.register(TamponNotification)
class TamponNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "created_at",
        "is_resolved",
    )
    list_filter = ("room__building", "room__floor_number", "is_resolved", "created_at")
    search_fields = (
        "room__room_number",
        "notification_text",
    )


@admin.register(Restock)
class RestockAdmin(admin.ModelAdmin):
    list_display = (
        "room",
        "restock_time",
        "restocked_by",
    )
    list_filter = ("room__building", "room__floor_number", "restock_time")
    search_fields = (
        "room__room_number",
        "restocked_by__username",
    )
    inlines = [RestockItemInline]


@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ("name", "restock_default", "stock_amount")
    search_fields = ("name",)
