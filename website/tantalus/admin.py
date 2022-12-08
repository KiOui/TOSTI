from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html

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
class TantalusOrderVenueAdmin(admin.ModelAdmin):
    """Tantalus Order Venue Admin."""

    list_display = [
        "order_venue",
        "endpoint_id",
    ]
    form = TantalusOrderVenueAdminForm


class TantalusShiftAdmin(ShiftAdmin):
    """Add sync to Tantalus button to ShiftAdmin."""

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add context to the extra_context."""
        try:
            obj = Shift.objects.get(id=object_id)
        except Shift.DoesNotExist:
            obj = None

        if extra_context is None:
            extra_context = {}

        extra_context["show_push_to_tantalus"] = obj is not None and obj.finalized
        return super(ShiftAdmin, self).change_view(request, object_id, form_url, extra_context)

    def _should_do_push_to_tantalus(self, obj, request):
        """Whether a push to tantalus should happen."""
        return obj and "_pushtotantalus" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""
        try:
            obj = Shift.objects.get(id=object_id)
        except Shift.DoesNotExist:
            obj = None

        if self._should_do_push_to_tantalus(obj, request):
            if synchronize_shift_to_tantalus(obj):
                self.message_user(request, format_html("Tantalus synchronisation succeeded."), messages.SUCCESS)
                TantalusShiftSynchronization.objects.get_or_create(shift=obj)
            else:
                self.message_user(
                    request,
                    format_html(
                        "Failed to synchronize data to Tantalus, please consult the server logs for more information."
                    ),
                    level=messages.ERROR,
                )
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(ShiftAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )

    def has_change_permission(self, request, obj=None):
        """Don't check change permissions when _pushtotantalus is present in POST parameters."""
        if self._should_do_push_to_tantalus(obj, request):
            return super(ShiftAdmin, self).has_change_permission(request, obj=obj)
        else:
            return super(TantalusShiftAdmin, self).has_change_permission(request, obj=obj)


class TantalusBorrelReservationAdmin(BorrelReservationAdmin):
    """Add sync to Tantalus button to BorrelReservationAdmin."""

    list_display = [
        "title",
        "association",
        "user_created",
        "start",
        "end",
        "accepted",
        "submitted",
        "pushed_to_tantalus",
    ]

    def pushed_to_tantalus(self, obj):
        """Reservation is pushed to Tantalus."""
        return TantalusBorrelReservationSynchronization.objects.filter(borrel_reservation=obj).exists()

    pushed_to_tantalus.boolean = True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add context to the extra_context."""
        try:
            obj = BorrelReservation.objects.get(id=object_id)
        except BorrelReservation.DoesNotExist:
            obj = None

        if extra_context is None:
            extra_context = {}

        synchronization_already_done = (
            obj is not None
            and TantalusBorrelReservationSynchronization.objects.filter(borrel_reservation=obj).exists()
        )

        extra_context["show_push_to_tantalus"] = obj is not None and obj.submitted and not synchronization_already_done
        extra_context["show_force_push_to_tantalus"] = (
            obj is not None and obj.submitted and synchronization_already_done
        )
        return super(BorrelReservationAdmin, self).change_view(request, object_id, form_url, extra_context)

    def _should_do_push_to_tantalus(self, obj, request):
        """Whether a push to tantalus should happen."""
        return obj and "_pushtotantalus" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""
        try:
            obj = BorrelReservation.objects.get(id=object_id)
        except BorrelReservation.DoesNotExist:
            obj = None

        if self._should_do_push_to_tantalus(obj, request):
            try:
                synchronize_borrelreservation_to_tantalus(obj)
                self.message_user(request, format_html("Tantalus synchronisation succeeded."), messages.SUCCESS)
                TantalusBorrelReservationSynchronization.objects.get_or_create(borrel_reservation=obj)
            except TantalusException as e:
                self.message_user(
                    request,
                    format_html(
                        "Failed to synchronize data to Tantalus, the following exception occurred: {}.".format(e)
                    ),
                    level=messages.ERROR,
                )
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(BorrelReservationAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )


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
