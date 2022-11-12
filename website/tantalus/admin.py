from django.contrib import admin, messages
from django.utils.html import format_html
from django_easy_admin_object_actions.admin import ObjectActionsMixin
from django_easy_admin_object_actions.decorators import object_action

from borrel.admin import BorrelReservationAdmin
from borrel.models import BorrelReservation
from orders.admin import ShiftAdmin
from orders.models import Shift
from tantalus.models import (
    TantalusOrdersProduct,
    TantalusOrderVenue,
    TantalusShiftSynchronization,
    TantalusBorrelProduct,
    TantalusAssociation,
    TantalusBorrelReservationSynchronization,
)
from tantalus.services import (
    synchronize_shift_to_tantalus,
    synchronize_borrelreservation_to_tantalus,
    TantalusException,
)
from tantalus.forms import (
    TantalusOrdersProductAdminForm,
    TantalusOrderVenueAdminForm,
    TantalusAssociationAdminForm,
    TantalusBorrelProductAdminForm,
)


@admin.register(TantalusOrdersProduct)
class TantalusOrdersProductAdmin(admin.ModelAdmin):
    """Tantalus Order Product Admin."""

    list_display = [
        "product",
        "tantalus_id",
    ]
    form = TantalusOrdersProductAdminForm


@admin.register(TantalusAssociation)
class TantalusAssociationAdmin(admin.ModelAdmin):
    """Tantalus Association Admin."""

    list_display = [
        "association",
        "tantalus_id",
    ]
    form = TantalusAssociationAdminForm


@admin.register(TantalusOrderVenue)
class TantalusOrderVenueAdmin(ObjectActionsMixin, admin.ModelAdmin):
    """Tantalus Order Venue Admin."""

    list_display = [
        "order_venue",
        "endpoint_id",
    ]
    form = TantalusOrderVenueAdminForm


class TantalusShiftAdmin(ShiftAdmin):
    """Add sync to Tantalus button to ShiftAdmin."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display.append("pushed_to_tantalus")
        self.object_actions_after_fieldsets.append("push_to_tantalus")

    @object_action(
        label="Push to Tantalus",
        perform_after_saving=True,
        confirmation="Are you sure you want to push this shift to Tantalus?",
        condition=lambda _, obj: obj.submitted,
        display_as_disabled_if_condition_not_met=True,
        log_message="Pushed to Tantalus",
    )
    def push_to_tantalus(self, request, obj):
        """Push to Tantalus."""
        try:
            synchronize_shift_to_tantalus(obj)
            self.message_user(request, format_html(
                "Tantalus synchronisation succeeded."), messages.SUCCESS)
            TantalusShiftSynchronization.objects.get_or_create(
                shift=obj)
        except TantalusException as e:
            self.message_user(
                request,
                format_html(
                    "Failed to synchronize data to Tantalus, the following exception occurred: {}.".format(
                        e)
                ),
                level=messages.ERROR,
            )
        return True

    object_actions_after_fieldsets = ["push_to_tantalus"]

    def pushed_to_tantalus(self, obj):
        """Shift is pushed to Tantalus."""
        return TantalusShiftSynchronization.objects.filter(shift=obj).exists()

    pushed_to_tantalus.boolean = True


class TantalusBorrelReservationAdmin(BorrelReservationAdmin):
    """Add sync to Tantalus button to BorrelReservationAdmin."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display.append("pushed_to_tantalus")
        self.readonly_fields += ("pushed_to_tantalus", )
        self.fieldsets[0][1]["fields"] += ("pushed_to_tantalus", )

        self.object_actions_after_fieldsets.append("push_to_tantalus")
        self.object_actions_after_fieldsets.append("force_push_to_tantalus")

    @object_action(
        label="Push to Tantalus",
        perform_after_saving=True,
        confirmation="Are you sure you want to push this shift to Tantalus?",
        condition=lambda _, obj: obj.submitted,
        display_as_disabled_if_condition_not_met=True,
        log_message="Pushed to Tantalus",
    )
    def push_to_tantalus(self, request, obj):
        """Push to Tantalus."""
        try:
            synchronize_borrelreservation_to_tantalus(obj)
            self.message_user(request, format_html(
                "Tantalus synchronisation succeeded."), messages.SUCCESS)
            TantalusBorrelReservationSynchronization.objects.get_or_create(
                borrel_reservation=obj)
        except TantalusException as e:
            self.message_user(
                request,
                format_html(
                    "Failed to synchronize data to Tantalus, the following exception occurred: {}.".format(
                        e)
                ),
                level=messages.ERROR,
            )
        return True

    @object_action(
        label="Force push to Tantalus",
        perform_after_saving=True,
        confirmation="This reservation was already pushed to Tantalus. Are you sure you want to push this shift to Tantalus again?",
        condition=lambda _, obj: self.pushed_to_tantalus(obj),
        display_as_disabled_if_condition_not_met=True,
        log_message="Force pushed to Tantalus",
        include_in_queryset_actions=False,
    )
    def force_push_to_tantalus(self, request, obj):
        self.push_to_tantalus(request, obj)

    def pushed_to_tantalus(self, obj):
        """Reservation is pushed to Tantalus."""
        return TantalusBorrelReservationSynchronization.objects.filter(borrel_reservation=obj).exists()

    pushed_to_tantalus.boolean = True


@admin.register(TantalusBorrelProduct)
class TantalusBorrelProductAdmin(admin.ModelAdmin):
    """Tantalus Borrel Product Admin."""

    list_display = [
        "product",
        "tantalus_id",
    ]
    form = TantalusBorrelProductAdminForm


# Register the Tantalus Shift admin instead of the normal Shift admin.
admin.site.unregister(Shift)
admin.site.register(Shift, TantalusShiftAdmin)

# Register the Tantalus BorrelReservation admin instead of the normal BorrelReservation admin.
admin.site.unregister(BorrelReservation)
admin.site.register(BorrelReservation, TantalusBorrelReservationAdmin)
