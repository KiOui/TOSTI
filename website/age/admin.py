from django.contrib import admin
from django.contrib.admin import register

from age.models import AgeRegistration


@register(AgeRegistration)
class AgeRegistrationAdmin(admin.ModelAdmin):
    """Admin interface for the age registration model."""

    list_display = ("user", "name", "minimum_age", "created_at")
    search_fields = ("user__username",)
    ordering = ("created_at",)

    def name(self, instance):
        """Name of the user."""
        return instance.user.__str__()
