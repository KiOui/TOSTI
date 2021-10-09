from django.contrib import admin
from .models import BasicBorrelBrevet


@admin.register(BasicBorrelBrevet)
class BasicBorrelBrevetAdmin(admin.ModelAdmin):
    """Custom admin for basic borrel brevet."""

    list_display = ["user", "registered_on", "has_certificate"]
    search_fields = ["user"]
