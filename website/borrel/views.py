from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView

from borrel.forms import BorrelReservationRequestForm, ReservationItemForm, ReservationItemSubmissionForm
from borrel.mixins import BasicBorrelBrevetRequiredMixin
from borrel.models import Product, BorrelReservation, ReservationItem
from venues.models import Venue


@method_decorator(login_required, name="dispatch")
class ReservationRequestCreateView(BasicBorrelBrevetRequiredMixin, CreateView):
    """Create view for Reservation Request."""

    template_name = "borrel/reservation_request_create.html"
    model = BorrelReservation
    form_class = BorrelReservationRequestForm

    def _get_inline_formset(self, data=None, instance=None):
        formset = inlineformset_factory(
            parent_model=BorrelReservation,
            model=ReservationItem,
            form=ReservationItemForm,
            can_delete=False,
            extra=Product.objects.available_products().count(),
            max_num=Product.objects.available_products().count(),
            validate_max=True,
            min_num=1,
            validate_min=True,
        )
        if data:
            return formset(data)
        elif instance:
            return formset(instance=instance)
        return formset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["items"] = self._get_inline_formset(self.request)
            for item, product in zip(context["items"], Product.objects.available_products()):
                item.initial = {"product": product}
        else:
            context["items"] = self._get_inline_formset()
            for item, product in zip(context["items"], Product.objects.available_products()):
                item.initial = {"product": product}
        return context

    def get_success_url(self):
        return reverse("borrel:add_reservation")

    def form_valid(self, form):
        context = self.get_context_data()
        items = context["items"]
        if items.is_valid():
            obj = form.save()
            items.instance = obj
            items.save()
            messages.add_message(self.request, messages.SUCCESS, "Your borrel reservation has been placed.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(ReservationRequestCreateView, self).get_form_kwargs()
        kwargs.update(
            {
                "request": self.request,
            }
        )
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
class ListReservationsView(ListView):
    model = BorrelReservation
    template_name = "borrel/reservation_list.html"

    def get_queryset(self):
        return super().get_queryset().filter(user__pk=self.request.user.pk)


@method_decorator(login_required, name="dispatch")
class ReservationView(UpdateView):
    model = BorrelReservation
    template_name = "borrel/reservation_request_submit.html"
    form_class = BorrelReservationRequestForm

    def get_queryset(self):
        return super().get_queryset().filter(user__pk=self.request.user.pk)

    def _get_inline_formset(self, data=None, instance=None):
        formset = inlineformset_factory(
            parent_model=BorrelReservation,
            model=ReservationItem,
            form=ReservationItemSubmissionForm,
            can_delete=False,
            extra=Product.objects.available_products().count(),
            max_num=Product.objects.available_products().count(),
            validate_max=True,
            min_num=1,
            validate_min=True,
        )
        if data:
            return formset(data)
        elif instance:
            return formset(instance=instance)
        return formset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["items"] = self._get_inline_formset(self.request.POST)
            for item, product in zip(context["items"], Product.objects.available_products()):
                item.initial = {"product": product}
        else:
            context["items"] = self._get_inline_formset(instance=self.get_object())
            for item, product in zip(context["items"], Product.objects.available_products()):
                item.initial = {"product": product}
        return context

    def get_success_url(self):
        return reverse("borrel:add_reservation")

    def form_valid(self, form):
        context = self.get_context_data()
        items = context["items"]
        if items.is_valid():
            obj = form.save()
            items.instance = obj
            items.save()
            messages.add_message(self.request, messages.SUCCESS, "Your borrel reservation has been saved.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)
