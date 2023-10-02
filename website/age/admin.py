from django.contrib import admin
from django.contrib.admin import register

from age.models import AgeRegistration
from age.forms import AgeRegistrationAdminForm


@register(AgeRegistration)
class AgeRegistrationAdmin(admin.ModelAdmin):
    """Admin interface for the age registration model."""

    list_display = ("user", "name", "minimum_age", "created_at")
    search_fields = ("user__username",)
    ordering = ("created_at",)
    form = AgeRegistrationAdminForm

    def get_exclude(self, request, obj=None):
        """Get excluded fields for the form."""
        if obj is not None and obj.verified_by_user is not None:
            return ["verified_by"]
        else:
            return ["verified_by_user"]

    def get_readonly_fields(self, request, obj=None):
        """Get readonly fields for the form."""
        if obj is not None and obj.verified_by_user is not None:
            return ["verified_by_user"]
        else:
            return ["verified_by"]

    def save_model(self, request, obj, form, change):
        """Add user_created when new object is created on admin panel."""
        obj.verified_by_user = request.user
        return super().save_model(request, obj, form, change)

    def name(self, instance):
        """Name of the user."""
        return instance.user.__str__()
