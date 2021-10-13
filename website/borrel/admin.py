from django.contrib import admin
from .models import BasicBorrelBrevet, ReservationRequest


@admin.register(BasicBorrelBrevet)
class BasicBorrelBrevetAdmin(admin.ModelAdmin):
    """Custom admin for basic borrel brevet."""

    list_display = ["user", "registered_on"]
    search_fields = ["user"]
    readonly_fields = ["registered_on"]


@admin.register(ReservationRequest)
class ReservationRequestAdmin(admin.ModelAdmin):
    """Custom admin for Reservation requests."""

    list_display = ["title", "association", "start_time", "end_time", "venue", "accepted"]
    search_fields = ["title", "user"]
    readonly_fields = ["accepted"]
