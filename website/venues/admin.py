from django.contrib import admin

from venues.models import Venue, Reservation


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    """Custom admin for venues."""

    search_fields = ["name"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Custom admin for reservations."""

    list_display = ["title", "venue", "start_time", "end_time", "user"]
    list_filter = ["venue", "user"]
    search_fields = ["title"]
    date_hierarchy = "start_time"
