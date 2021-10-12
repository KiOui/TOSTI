from django.contrib import admin
from django import forms
from django.db.models import Q

from venues.models import Venue, Reservation


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    """Custom admin for venues."""

    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


class ReservationAdminForm(forms.ModelForm):
    """Admin form to edit forms."""

    class Meta:
        """Meta class for ReservationAdminForm."""

        model = Reservation
        exclude = []

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if not instance:
            self.fields["venue"].queryset = Venue.objects.filter(can_be_reserved=True)
        else:
            self.fields["venue"].queryset = Venue.objects.filter(Q(can_be_reserved=True) | Q(pk=instance.pk))


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Custom admin for reservations."""

    list_display = ["title", "venue", "start_time", "end_time", "user"]
    list_filter = ["venue", "user"]
    search_fields = ["title"]
    date_hierarchy = "start_time"
    form = ReservationAdminForm
