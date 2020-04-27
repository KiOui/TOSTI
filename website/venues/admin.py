from django.contrib import admin

from venues.models import Venue


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    """Custom admin for venues."""
