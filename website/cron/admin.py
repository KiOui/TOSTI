from datetime import timedelta

from django.contrib import admin
from django.db.models import DurationField, ExpressionWrapper, F
from django.utils.translation import gettext_lazy as _

from cron.models import CronJobLog, CronJobLock
from cron.helpers import humanize_duration


class DurationFilter(admin.SimpleListFilter):
    """Filter for filtering on duration of a cron job."""

    title = _("duration")
    parameter_name = "duration"

    def lookups(self, request, model_admin):
        """Lookup options."""
        return (
            ("lte_minute", _("<= 1 minute")),
            ("gt_minute", _("> 1 minute")),
            ("gt_hour", _("> 1 hour")),
            ("gt_day", _("> 1 day")),
        )

    def queryset(self, request, queryset):
        """Filter the queryset."""
        if self.value() == "lte_minute":
            return queryset.filter(end_time__lte=F("start_time") + timedelta(minutes=1))
        if self.value() == "gt_minute":
            return queryset.filter(end_time__gt=F("start_time") + timedelta(minutes=1))
        if self.value() == "gt_hour":
            return queryset.filter(end_time__gt=F("start_time") + timedelta(hours=1))
        if self.value() == "gt_day":
            return queryset.filter(end_time__gt=F("start_time") + timedelta(days=1))


@admin.register(CronJobLog)
class CronJobLogAdmin(admin.ModelAdmin):
    """Admin for cron job logs."""

    search_fields = ("code", "message")
    ordering = ("-start_time",)
    list_display = ("code", "start_time", "end_time", "humanize_duration", "is_success")
    list_filter = ("code", "start_time", "is_success", DurationFilter)

    def get_queryset(self, request):
        """Retrieve the queryset."""
        return (
            super()
            .get_queryset(request)
            .annotate(
                duration=ExpressionWrapper(
                    F("end_time") - F("start_time"), DurationField()
                ),
            )
        )

    def get_readonly_fields(self, request, obj=None):
        """Make all fields read-only if not superuser."""
        if not request.user.is_superuser and obj is not None:
            names = [f.name for f in CronJobLog._meta.fields if f.name != "id"]
            return self.readonly_fields + tuple(names)
        return self.readonly_fields

    def humanize_duration(self, obj):
        """Humanize a duration."""
        return humanize_duration(obj.end_time - obj.start_time)

    humanize_duration.short_description = _("Duration")
    humanize_duration.admin_order_field = "duration"


@admin.register(CronJobLock)
class CronJobLockAdmin(admin.ModelAdmin):
    """Admin for cron job locks."""

    pass
