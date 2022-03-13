from django.contrib import admin

from . import models
from .settings import settings


@admin.register(models.Setting)
class SettingAdmin(admin.ModelAdmin):
    """Setting Admin."""

    model = models.Setting

    list_display = ["slug", "value", "type", "nullable", "in_use"]
    fields = ["slug", "value", "type", "nullable", "in_use"]
    readonly_fields = ["slug", "type", "nullable", "in_use"]
    search_fields = ["slug", "value"]
    list_filter = ["type", "nullable"]

    def in_use(self, obj):
        """Get in use."""
        return settings.is_registered(obj.slug)

    in_use.boolean = True

    def has_delete_permission(self, request, obj=None):
        """Get delete permission."""
        return obj is None or not settings.is_registered(obj.slug)
