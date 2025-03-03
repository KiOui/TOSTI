from django.contrib import admin
from import_export.admin import ExportMixin

from qualifications.models import BasicBorrelBrevet
from qualifications.resources import BasicBorrelBrevetResource


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
