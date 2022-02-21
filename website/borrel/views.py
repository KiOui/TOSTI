from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from borrel import models
from borrel.forms import BorrelReservationRequestForm
from borrel.mixins import BasicBorrelBrevetRequiredMixin
from borrel.selectors import product_categories, available_products
from venues.models import Venue


class AllCalendarView(TemplateView):
    """All venues calendar view."""

    template_name = "borrel/calendar.html"

    def get(self, request, **kwargs):
        has_borrel_brevet = request.user.is_authenticated and models.BasicBorrelBrevet.objects.filter(user=request.user).exists()
        return render(request, self.template_name, {"can_request_reservation": has_borrel_brevet})


class VenueCalendarView(TemplateView):
    """Specific Venue calendar view."""

    template_name = "borrel/venue_calendar.html"

    def get(self, request, **kwargs):
        venue = kwargs.get("venue")
        has_borrel_brevet = request.user.is_authenticated and models.BasicBorrelBrevet.objects.filter(user=request.user).exists()
        return render(request, self.template_name, {"venue": venue, "can_request_reservation": has_borrel_brevet})


class ReservationRequestCreateView(BasicBorrelBrevetRequiredMixin, FormView):
    """Create view for Reservation Request."""

    template_name = "borrel/reservation_request_create.html"
    form_class = BorrelReservationRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = product_categories()
        context['products_no_category'] = available_products().filter(category=None)
        return context

    def get_success_url(self):
        return reverse("borrel:reservation_request_create")

    def _add_line_items_to_reservation(self, reservation):
        created_items = list()
        form_keys = self.request.POST.keys()
        for form_key in form_keys:
            if form_key.startswith("product_"):
                product_id = form_key.split('_', 1)[1]
                try:
                    product = models.Product.objects.get(id=product_id)
                    product_amount = int(self.request.POST[form_key])
                    created_items.append(models.ReservationItem.objects.create(reservation=reservation, product=product, product_name=product.name, product_description=product.description, product_price_per_unit=product.price, amount_reserved=product_amount))
                except models.Product.DoesNotExist:
                    # When the product can not be found
                    pass
                except ValueError:
                    # When string is passed to product_id or value product_amount can not be converted to int
                    pass
        return created_items

    def form_valid(self, form):
        reservation = form.save()
        self._add_line_items_to_reservation(reservation)
        messages.add_message(self.request, messages.SUCCESS, "Your reservation has been placed.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(ReservationRequestCreateView, self).get_form_kwargs()
        kwargs.update(
            {
                "request": self.request,
            }
        )
        preset_venue = self.request.GET.get('venue', None)
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
