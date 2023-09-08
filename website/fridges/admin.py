from django.contrib import admin
from django.contrib.admin import register
from guardian.admin import GuardedModelAdmin

from fridges.models import Fridge, GeneralOpeningHours, AccessLog, BlacklistEntry


class GeneralOpeningHoursInline(admin.TabularInline):
    """Inline for the GeneralOpeningHours model."""

    model = GeneralOpeningHours
    extra = 0


@register(Fridge)
class FridgeAdmin(GuardedModelAdmin):
    """Admin for the Fridge model."""

    inlines = [GeneralOpeningHoursInline]
    prepopulated_fields = {"slug": ("name",)}
    list_display = ["name", "venue", "is_active", "last_opened", "last_opened_by"]


@register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """Admin for the AccessLog model."""

    list_display = ["user", "fridge", "timestamp"]
    list_filter = ["fridge", "timestamp"]
    search_fields = ["user__username", "user__first_name", "user__last_name"]
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        """Disable the add permission."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable the change permission."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable the delete permission."""
        return False


@register(BlacklistEntry)
class BlacklistEntryAdmin(admin.ModelAdmin):
    """Admin for the BlacklistEntry model."""

    autocomplete_fields = ["user"]
