from autocompletefilter.admin import AutocompleteFilterMixin
from autocompletefilter.filters import AutocompleteListFilter
from django.contrib import admin
from django.contrib.admin.models import LogEntry

admin.site.site_header = "T.O.S.T.I. Admin"
admin.site.site_title = "TOSTI"


@admin.register(LogEntry)
class LogEntryAdmin(AutocompleteFilterMixin, admin.ModelAdmin):
    """Admin for the LogEntry model."""

    date_hierarchy = "action_time"

    list_filter = [("user", AutocompleteListFilter), "content_type", "action_flag"]

    search_fields = ["object_repr", "change_message"]

    list_display = [
        "action_time",
        "user",
        "object_repr",
        "action_flag",
    ]

    def has_add_permission(self, request):
        """Allow adding of the log."""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow changing of the log."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deleting of the log."""
        return False

    def has_view_permission(self, request, obj=None):
        """Allow viewing of the log."""
        return True
