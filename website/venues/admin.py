from admin_auto_filters.filters import AutocompleteFilter
from django.contrib import admin, messages
from django import forms
from django.db.models import Q
from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from venues.models import Venue, Reservation


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    """Custom admin for venues."""

    list_display = ["name", "slug", "active", "can_be_reserved"]
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


class ReservationAdminUserFilter(AutocompleteFilter):
    """Filter class to filter product objects available at a certain venue."""

    title = "User"
    field_name = "user"


@admin.register(Reservation)
class ReservationAdmin(ObjectActionsMixin, admin.ModelAdmin):
    """Custom admin for reservations."""

    list_display = ["title", "venue", "association", "start", "end", "user", "accepted"]
    list_filter = [
        "venue",
        "association",
        "start",
        "accepted",
        "start",
    ]
    search_fields = ["title"]
    autocomplete_fields = ["user"]
    # date_hierarchy = "start"
    form = ReservationAdminForm

    readonly_fields = ["accepted"]

    @object_action(
        label="Accept",
        perform_after_saving=True,
        permission="venues.change_reservation",
        extra_classes="default",
        condition=lambda _, obj: not obj.accepted == True,
        display_as_disabled_if_condition_not_met=True,
        log_message="Accepted",
    )
    def accept(self, request, obj):
        """Accept a reservation."""
        obj.accepted = True
        obj.save()
        return True

    @object_action(
        label="Reject",
        perform_after_saving=True,
        permission="venues.change_reservation",
        condition=lambda _, obj: not obj.accepted == False,
        display_as_disabled_if_condition_not_met=True,
        log_message="Rejected",
    )
    def reject(self, request, obj):
        """Accept a reservation."""
        obj.accepted = False
        obj.save()
        return True

    object_actions_after_related_objects = ["accept", "reject"]


    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Display warning for overlapping reservations."""
        if object_id:
            obj = self.get_object(request, object_id)
            if (
                Reservation.objects.filter(venue=obj.venue)
                .filter(
                    Q(start__lte=obj.start, end__gt=obj.start)
                    | Q(start__lt=obj.end, end__gte=obj.end)
                    | Q(start__gte=obj.start, end__lte=obj.end)
                )
                .exclude(pk=obj.pk)
                .exists()
            ):
                self.message_user(
                    request,
                    "This reservation overlaps with another reservation for the same venue.",
                    level=messages.WARNING,
                )
        return super().changeform_view(request, object_id, form_url, extra_context)

    class Media:
        """Necessary to use AutocompleteFilter."""
