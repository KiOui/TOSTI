from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView, FormView, DeleteView

from borrel.forms import (
    BorrelReservationRequestForm,
    ReservationItemForm,
    ReservationItemSubmissionForm,
    BorrelReservationSubmissionForm,
    BorrelReservationUpdateForm,
    ReservationItemDisabledForm,
    BorrelReservationDisabledForm,
)
from borrel.mixins import BasicBorrelBrevetRequiredMixin
from borrel.models import Product, BorrelReservation, ReservationItem, ProductCategory
from venues.models import Venue


class ReservationRequestBaseView(FormView):
    model = BorrelReservation
    inline_form_class = ReservationItemForm

    def get_inline_form_class(self):
        return self.inline_form_class

    def _get_inline_formset(self, data=None, instance=None, files=None):
        """Create and populate a formset."""
        formset = inlineformset_factory(
            parent_model=BorrelReservation,
            model=ReservationItem,
            form=self.get_inline_form_class(),
            can_delete=True,
            extra=Product.objects.available_products().count(),
            max_num=Product.objects.available_products().count(),
            validate_max=True,
            min_num=1,
            validate_min=True,
        )
        if data and instance:
            return formset(data=data, instance=instance, files=files)
        elif data:
            return formset(data=data, files=files)
        elif instance:
            return formset(instance=instance, files=files)
        return formset()

    def _initialize_forms(self, forms, products):
        """Fill formset forms with data for products."""
        assert len(forms) == len(products)
        for item, product in zip(forms, products):
            # Note that this puts the full product object in the product field, not just the pk as would be default behaviour. This is done so that when sorting the formset, the category and immediately be accessed.
            item.initial.update(
                {
                    "product": product,
                    "product_name": product.name,
                    "product_description": product.description,
                    "product_price_per_unit": product.price,
                }
            )

    def _sort_formset(self, formset):
        """Sort the forms in a formset based on category."""
        # First, replace the initial product id's in the form for full product objects
        # This is not required for the extra_forms, as those are already initialized with full objects by `_initialize_forms()`
        for form in formset.forms:
            if type(form.initial["product"]) == int:
                form.initial["product"] = Product.objects.get(id=form.initial["product"])

        # Do the actual sorting
        formset.forms.sort(
            key=lambda x: (
                x.initial["product"].category.id
                if x.initial["product"].category
                else ProductCategory.objects.latest("pk").pk + 1,
                x.initial["product"].name,
            )
        )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(user_created__pk=self.request.user.pk)
                | Q(pk__in=self.request.user.borrel_reservations_access.values("pk"))
            )
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request": self.request})
        preset_venue = self.request.GET.get("venue", None)
        if preset_venue is not None:
            try:
                venue = Venue.objects.get(id=preset_venue)
                kwargs.update(
                    {
                        "initial": {
                            "venue": venue.id,
                        }
                    }
                )
            except Venue.DoesNotExist:
                pass
            except ValueError:
                pass
        return kwargs


@method_decorator(login_required, name="dispatch")
class ReservationRequestCreateView(BasicBorrelBrevetRequiredMixin, ReservationRequestBaseView, CreateView):
    """Create a new reservation (request)."""

    template_name = "borrel/reservation_request_create.html"
    form_class = BorrelReservationRequestForm
    inline_form_class = ReservationItemForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context["items"] = self._get_inline_formset(data=self.request.POST)
        else:
            context["items"] = self._get_inline_formset()

        self._initialize_forms(context["items"].forms, Product.objects.available_products())
        self._sort_formset(context["items"])

        return context

    def get_success_url(self):
        return reverse("borrel:list_reservations")

    def form_valid(self, form):
        context = self.get_context_data()
        items = context["items"]
        if items.is_valid():
            obj = form.save()
            obj.user_created = self.request.user
            obj.save()
            items.instance = obj
            items.save()
            messages.add_message(self.request, messages.SUCCESS, "Your borrel reservation has been placed.")
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.add_message(self.request, messages.ERROR, "Something went wrong.")
            return self.form_invalid(form)


class ReservationRequestUpdateView(BasicBorrelBrevetRequiredMixin, ReservationRequestBaseView, UpdateView):
    """View and update a reservation"""

    template_name = "borrel/reservation_request_view.html"

    def get_form_class(self):
        if self.get_object().can_be_changed:
            return BorrelReservationUpdateForm
        else:
            return BorrelReservationDisabledForm

    def get_inline_form_class(self):
        if self.get_object().can_be_changed:
            return ReservationItemForm
        else:
            return ReservationItemDisabledForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.available_products()
        products_reserved = self.get_object().items.values_list("product")
        new_products = products.exclude(id__in=products_reserved)

        if self.request.POST:
            context["items"] = self._get_inline_formset(data=self.request.POST, instance=self.get_object())
            self._initialize_forms(context["items"].extra_forms, new_products)
        else:
            context["items"] = self._get_inline_formset(instance=self.get_object())
            self._initialize_forms(context["items"].extra_forms, new_products)
            self._sort_formset(context["items"])

        return context

    def get_success_url(self):
        return reverse("borrel:view_reservation", kwargs={"pk": self.get_object().pk})

    def form_valid(self, form):
        if not self.get_object().can_be_changed:
            return HttpResponseRedirect(self.get_success_url())

        context = self.get_context_data()
        items = context["items"]
        if items.is_valid():
            obj = form.save()
            obj.user_updated = self.request.user
            obj.updated_at = timezone.now()
            obj.save()
            items.instance = obj
            items.save()
            messages.add_message(self.request, messages.SUCCESS, "Your borrel reservation has been updated.")
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.add_message(self.request, messages.ERROR, f"Something went wrong. {items.errors}")
            return self.form_invalid(form)


class ReservationRequestCancelView(DeleteView):
    """Delete a reservation request if it is not yet accepted."""

    model = BorrelReservation
    template_name = "borrel/reservation_request_cancel.html"

    def get_success_url(self):
        return reverse("borrel:list_reservations")

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().can_be_changed:
            messages.add_message(
                self.request,
                messages.ERROR,
                "Your borrel reservation cannot be cancelled anymore, as it is already accepted.",
            )
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ListReservationsView(ListView):
    model = BorrelReservation
    template_name = "borrel/reservation_list.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(user_created__pk=self.request.user.pk)
                | Q(pk__in=self.request.user.borrel_reservations_access.values("pk"))
            )
        )


@method_decorator(login_required, name="dispatch")
class JoinReservationView(BasicBorrelBrevetRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            reservation = BorrelReservation.objects.get(join_code=self.kwargs.get("code"))
        except BorrelReservation.DoesNotExist:
            messages.add_message(self.request, messages.INFO, "Invalid code.")
            return HttpResponseRedirect(reverse("index"))

        if self.request.user not in reservation.users_access.all():
            reservation.users_access.add(self.request.user)
            reservation.save()
            messages.add_message(self.request, messages.INFO, "You now have access to this reservation.")

        return HttpResponseRedirect(reverse("borrel:view_reservation", kwargs={"pk": reservation.pk}))


class ReservationRequestSubmitView(BasicBorrelBrevetRequiredMixin, ReservationRequestBaseView, UpdateView):
    """View and update a reservation"""

    template_name = "borrel/reservation_request_submit.html"
    form_class = BorrelReservationSubmissionForm
    inline_form_class = ReservationItemSubmissionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.available_products()
        products_reserved = self.get_object().items.values_list("product")
        new_products = products.exclude(id__in=products_reserved)

        if self.request.POST:
            context["items"] = self._get_inline_formset(data=self.request.POST, instance=self.get_object())
            self._initialize_forms(context["items"].extra_forms, new_products)
        else:
            context["items"] = self._get_inline_formset(instance=self.get_object())
            self._initialize_forms(context["items"].extra_forms, new_products)
            self._sort_formset(context["items"])

        return context

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().submitted:
            messages.add_message(self.request, messages.INFO, "Your borrel reservation was already submitted.")
            return HttpResponseRedirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("borrel:view_reservation", kwargs={"pk": self.get_object().pk})

    def form_valid(self, form):
        if self.get_object().submitted:
            messages.add_message(self.request, messages.INFO, "Your borrel reservation was already submitted.")
            return HttpResponseRedirect(self.get_success_url())

        context = self.get_context_data()
        items = context["items"]
        if items.is_valid():
            obj = form.save()
            obj.user_submitted = self.request.user
            obj.submitted_at = timezone.now()
            obj.save()
            items.instance = obj
            items.save()
            messages.add_message(self.request, messages.SUCCESS, "Your borrel reservation is submitted.")
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.add_message(self.request, messages.ERROR, f"Something went wrong. {items.errors}")
            return self.form_invalid(form)