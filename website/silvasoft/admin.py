from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from borrel.admin import BorrelReservationAdmin
from borrel.models import BorrelReservation
from orders.admin import ShiftAdmin
from orders.models import Shift
from silvasoft.forms import (
    SilvasoftAssociationAdminForm,
    SilvasoftOrderProductAdminForm,
    SilvasoftBorrelProductAdminForm,
    SilvasoftOrderVenueAdminForm,
)
from silvasoft.models import (
    SilvasoftShiftSynchronization,
    SilvasoftBorrelReservationSynchronization,
    SilvasoftAssociation,
    SilvasoftOrderProduct,
    SilvasoftBorrelProduct,
    SilvasoftOrderVenue,
    SilvasoftShiftInvoice,
    SilvasoftBorrelReservationInvoice,
)
from silvasoft.services import (
    synchronize_shift_to_silvasoft,
    synchronize_borrelreservation_to_silvasoft,
    SilvasoftException,
    get_silvasoft_client,
    refresh_cached_relations,
    refresh_cached_products,
)


@admin.register(SilvasoftAssociation)
class SilvasoftAssociationAdmin(admin.ModelAdmin):
    """Silvasoft Association Admin."""

    list_display = [
        "association",
        "silvasoft_customer_number",
    ]
    form = SilvasoftAssociationAdminForm

    def _should_refresh_relations(self, request):
        """Whether a relations refresh should happen."""
        return "_refreshrelations" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""

        if self._should_refresh_relations(request):
            try:
                refresh_cached_relations()
            except SilvasoftException:
                self.message_user(
                    request,
                    format_html(
                        "Failed to refresh relations from Silvasoft, please consult the server logs for more "
                        "information."
                    ),
                    level=messages.ERROR,
                )
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(SilvasoftAssociationAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )


@admin.register(SilvasoftOrderVenue)
class SilvasoftOrderVenueAdmin(admin.ModelAdmin):
    """Silvasoft Order Venue Admin."""

    list_display = [
        "order_venue",
        "silvasoft_customer_number",
    ]
    form = SilvasoftOrderVenueAdminForm

    def _should_refresh_relations(self, request):
        """Whether a relations refresh should happen."""
        return "_refreshrelations" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""

        if self._should_refresh_relations(request):
            try:
                refresh_cached_relations()
            except SilvasoftException:
                self.message_user(
                    request,
                    format_html(
                        "Failed to refresh relations from Silvasoft, please consult the server logs for more "
                        "information."
                    ),
                    level=messages.ERROR,
                )
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(SilvasoftOrderVenueAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )


@admin.register(SilvasoftOrderProduct)
class SilvasoftOrderProductAdmin(admin.ModelAdmin):
    """Silvasoft Order Product Admin."""

    list_display = [
        "product",
        "silvasoft_product_number",
    ]
    form = SilvasoftOrderProductAdminForm

    def _should_refresh_products(self, request):
        """Whether a products refresh should happen."""
        return "_refreshproducts" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""

        if self._should_refresh_products(request):
            try:
                refresh_cached_products()
            except SilvasoftException:
                self.message_user(
                    request,
                    format_html(
                        "Failed to refresh products from Silvasoft, please consult the server logs for more "
                        "information."
                    ),
                    level=messages.ERROR,
                )
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(SilvasoftOrderProductAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )


@admin.register(SilvasoftBorrelProduct)
class SilvasoftBorrelProductAdmin(admin.ModelAdmin):
    """Silvasoft Borrel Product Admin."""

    list_display = [
        "product",
        "silvasoft_product_number",
    ]
    form = SilvasoftBorrelProductAdminForm

    def _should_refresh_products(self, request):
        """Whether a products refresh should happen."""
        return "_refreshproducts" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""

        if self._should_refresh_products(request):
            try:
                refresh_cached_products()
            except SilvasoftException:
                self.message_user(
                    request,
                    format_html(
                        "Failed to refresh products from Silvasoft, please consult the server logs for more "
                        "information."
                    ),
                    level=messages.ERROR,
                )
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(SilvasoftBorrelProductAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )


class SilvasoftShiftAdmin(ShiftAdmin):
    """Add sync to Silvasoft button to ShiftAdmin."""

    list_display = [
        "date",
        "start_time",
        "end_time",
        "venue",
        "capacity",
        "get_is_active",
        "can_order",
        "finalized",
        "pushed_to_silvasoft",
    ]

    def pushed_to_silvasoft(self, obj):
        """Reservation is pushed to Silvasoft."""
        return SilvasoftShiftSynchronization.objects.filter(shift=obj, succeeded=True).exists()

    pushed_to_silvasoft.boolean = True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add context to the extra_context."""
        try:
            obj = Shift.objects.get(id=object_id)
        except Shift.DoesNotExist:
            obj = None

        if extra_context is None:
            extra_context = {}

        extra_context["show_push_to_silvasoft"] = obj is not None and obj.finalized
        return super(ShiftAdmin, self).change_view(request, object_id, form_url, extra_context)

    def _should_do_push_to_silvasoft(self, obj, request):
        """Whether a push to Silvasoft should happen."""
        return obj and "_pushtosilvasoft" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""
        try:
            obj = Shift.objects.get(id=object_id)
        except Shift.DoesNotExist:
            obj = None

        if self._should_do_push_to_silvasoft(obj, request):
            silvasoft_invoice, _ = SilvasoftShiftInvoice.objects.get_or_create(shift=obj)
            try:
                synchronize_shift_to_silvasoft(obj, silvasoft_invoice.silvasoft_identifier)
                self.message_user(request, format_html("Silvasoft synchronisation succeeded."), messages.SUCCESS)
                SilvasoftShiftSynchronization.objects.create(shift=obj, succeeded=True)
            except SilvasoftException:
                self.message_user(
                    request,
                    format_html(
                        "Failed to synchronize data to Silvasoft, the following exception occurred: '{}'.".format(e)
                    ),
                    level=messages.ERROR,
                )
                SilvasoftShiftSynchronization.objects.create(shift=obj, succeeded=False)
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(ShiftAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )

    def has_change_permission(self, request, obj=None):
        """Don't check change permissions when _pushtosilvasoft is present in POST parameters."""
        if self._should_do_push_to_silvasoft(obj, request):
            return super(ShiftAdmin, self).has_change_permission(request, obj=obj)
        else:
            return super(SilvasoftShiftAdmin, self).has_change_permission(request, obj=obj)


class SilvasoftBorrelReservationAdmin(BorrelReservationAdmin):
    """Add sync to Silvasoft button to BorrelReservationAdmin."""

    list_display = [
        "title",
        "association",
        "user_created",
        "start",
        "end",
        "accepted",
        "submitted",
        "pushed_to_silvasoft",
    ]

    def pushed_to_silvasoft(self, obj):
        """Reservation is pushed to Silvasoft."""
        return SilvasoftBorrelReservationSynchronization.objects.filter(
            borrel_reservation=obj, succeeded=True
        ).exists()

    pushed_to_silvasoft.boolean = True

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
            and SilvasoftBorrelReservationSynchronization.objects.filter(
                borrel_reservation=obj, succeeded=True
            ).exists()
        )

        extra_context["show_push_to_silvasoft"] = (
            obj is not None and obj.submitted and not synchronization_already_done
        )
        extra_context["show_force_push_to_silvasoft"] = (
            obj is not None and obj.submitted and synchronization_already_done
        )
        return super(BorrelReservationAdmin, self).change_view(request, object_id, form_url, extra_context)

    def _should_do_push_to_silvasoft(self, obj, request):
        """Whether a push to Silvasoft should happen."""
        return obj and "_pushtosilvasoft" in request.POST

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Add extra action to admin post request."""
        try:
            obj = BorrelReservation.objects.get(id=object_id)
        except BorrelReservation.DoesNotExist:
            obj = None

        if self._should_do_push_to_silvasoft(obj, request):
            silvasoft_invoice, _ = SilvasoftBorrelReservationInvoice.objects.get_or_create(borrel_reservation=obj)
            try:
                synchronize_borrelreservation_to_silvasoft(obj, silvasoft_invoice.silvasoft_identifier)
                self.message_user(request, format_html("Silvasoft synchronisation succeeded."), messages.SUCCESS)
                SilvasoftBorrelReservationSynchronization.objects.create(borrel_reservation=obj, succeeded=True)
            except SilvasoftException as e:
                self.message_user(
                    request,
                    format_html(
                        "Failed to synchronize data to Silvasoft, the following exception occurred: '{}'.".format(e)
                    ),
                    level=messages.ERROR,
                )
                SilvasoftBorrelReservationSynchronization.objects.create(borrel_reservation=obj, succeeded=False)
            redirect_url = request.path
            return HttpResponseRedirect(redirect_url)
        else:
            return super(BorrelReservationAdmin, self).changeform_view(
                request, object_id=object_id, form_url=form_url, extra_context=extra_context
            )


# Register the Silvasoft Shift admin instead of the normal Shift admin.
admin.site.unregister(Shift)
admin.site.register(Shift, SilvasoftShiftAdmin)

# Register the Silvasoft BorrelReservation admin instead of the normal BorrelReservation admin.
admin.site.unregister(BorrelReservation)
admin.site.register(BorrelReservation, SilvasoftBorrelReservationAdmin)
