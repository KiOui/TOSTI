from django.contrib import admin
from django.contrib.admin import register

from age.models import AgeRegistration
from age.forms import AgeRegistrationAdminForm


@register(AgeRegistration)
class AgeRegistrationAdmin(admin.ModelAdmin):
    """Admin interface for the age registration model."""

    list_display = (
        "user",
        "name",
        "minimum_age",
        "verified_by",
        "created_at",
    )
    search_fields = ("user__username",)
    ordering = ("created_at",)
    form = AgeRegistrationAdminForm
    autocomplete_fields = ["user"]

    def get_exclude(self, request, obj=None):
        """Get excluded fields for the form."""
        excluded = super().get_exclude(request, obj) or []

        if not obj or obj.verified_by != AgeRegistration.YIVI:
            excluded += ["attributes"]

        return excluded

    def get_readonly_fields(self, request, obj=None):
        """Get readonly fields for the form."""
        readonly_fields = super().get_readonly_fields(request, obj) or []

        if obj and obj.verified_by == AgeRegistration.MANUAL:
            readonly_fields += ["verified_by_user"]
        else:
            readonly_fields += ["verified_by"]

        if obj and obj.verified_by == AgeRegistration.YIVI:
            readonly_fields = ["user", "minimum_age", "verified_by", "attributes"]

        return readonly_fields

    def save_model(self, request, obj, form, change):
        """Add user_created when new object is created on admin panel."""
        obj.verified_by = AgeRegistration.MANUAL
        obj.verified_by_user = request.user
        return super().save_model(request, obj, form, change)

    def name(self, instance):
        """Name of the user."""
        return instance.user.__str__()
