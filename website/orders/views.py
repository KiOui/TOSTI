from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView, CreateView
from guardian.shortcuts import get_objects_for_user

from orders import services
from django.shortcuts import render, redirect

from tosti.utils import log_action
from .models import Order, Shift
from .forms import CreateShiftForm
from .services import user_is_blacklisted, user_can_manage_shift, user_can_manage_shifts_in_venue


class ShiftView(LoginRequiredMixin, TemplateView):
    """Overview page of a shift for regular users that also allows placing orders."""

    template_name = "orders/shift_overview.html"

    def get_context_data(self, **kwargs):
        """Get context data."""
        context = super(ShiftView, self).get_context_data(**kwargs)
        shift = kwargs.get("shift")
        context.update(
            {
                "shift": shift,
                "can_manage_shift": self.request.user.is_authenticated
                and user_can_manage_shift(self.request.user, shift),
                "has_order_permissions": self.request.user.is_authenticated
                and not user_is_blacklisted(self.request.user),
            },
        )
        return context


class ShiftManagementView(LoginRequiredMixin, TemplateView):
    """View for managing shifts."""

    template_name = "orders/shift_admin.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect users that haven't joined the shift to the join page."""
        shift = kwargs.get("shift")
        if not user_can_manage_shift(request.user, shift):
            return redirect("orders:shift_join", shift=shift)
        return super(ShiftManagementView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Get context data."""
        context = super(ShiftManagementView, self).get_context_data(**kwargs)
        shift = kwargs.get("shift")
        context.update(
            {"shift": shift, "has_change_order_permissions": user_can_manage_shift(self.request.user, shift)},
        )
        return context


class CreateShiftView(LoginRequiredMixin, CreateView):
    """Create shift view."""

    template_name = "orders/create_shift.html"
    form_class = CreateShiftForm
    model = Shift

    def dispatch(self, request, *args, **kwargs):
        """Only allow users that can manage the venue to create shifts."""
        venue = kwargs.get("venue")
        if not user_can_manage_shifts_in_venue(request.user, venue):
            raise PermissionDenied
        return super(CreateShiftView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """Return to the shift admin after creating the shift."""
        return reverse("orders:shift_admin", kwargs={"shift": self.object})

    def get_form_kwargs(self):
        """Pass the selected venue and user to the form."""
        kwargs = super(CreateShiftView, self).get_form_kwargs()
        extra_kwargs = {
            "venue": self.kwargs.get("venue"),
            "user": self.request.user,
        }
        return {**kwargs, **extra_kwargs}

    def get_context_data(self, **kwargs):
        """Get context data."""
        context = super(CreateShiftView, self).get_context_data(**kwargs)
        context.update(
            {
                "venue": kwargs.get("venue"),
            }
        )
        return context

    def form_valid(self, form):
        """Add user to the assignees list after creating the shift."""
        response = super(CreateShiftView, self).form_valid(form)
        log_action(self.request.user, self.object, ADDITION, "Created shift via website.")
        self.object.assignees.add(self.request.user.id)
        self.object.save()
        return response


class JoinShiftView(LoginRequiredMixin, TemplateView):
    """Join shift view."""

    template_name = "orders/join_shift.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect already joined users to the management page and disallow for users without permissions."""
        shift = kwargs.get("shift")
        assignees = shift.assignees.all()
        if request.user in assignees:
            return redirect("orders:shift_admin", shift=shift)
        if not user_can_manage_shifts_in_venue(request.user, shift.venue):
            raise PermissionDenied
        return super(JoinShiftView, self).dispatch(request, *args, **kwargs)

    def post(self, request, **kwargs):
        """Make users join the shift on POST."""
        shift = kwargs.get("shift")

        confirm = request.POST.get("confirm", None)
        if confirm == "Yes":
            services.add_user_to_assignees_of_shift(request.user, shift)
            log_action(request.user, shift, CHANGE, "Joined shift via website.")
            return redirect("orders:shift_admin", shift=shift)
        elif confirm == "No":
            return redirect("index")
        else:
            return render(request, self.template_name, {"shift": shift})


class AccountHistoryTabView(LoginRequiredMixin, TemplateView):
    """Account order history view."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """GET request for account history view."""
        ordered_items = Order.objects.filter(user=request.user).order_by("-created")
        page = request.GET.get("page", 1)
        paginator = Paginator(ordered_items, per_page=50)
        rendered_tab = render_to_string(
            "orders/account_history.html",
            context={"page_obj": paginator.get_page(page)},
        )
        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": rendered_tab,
            },
        )


def explainer_page_how_to_order_tab(request, item):
    """Render the explainer how to order tab."""
    return render_to_string("orders/explainer.html", context={"request": request, "item": item})


def explainer_page_how_to_manage_shift_tab(request, item):
    """Render the explainer how to manage shift tab."""
    if (
        request.user.is_authenticated
        and get_objects_for_user(request.user, "orders.can_manage_shift_in_venue").exists()
    ):
        return render_to_string("orders/explainer_admin.html", context={"request": request, "item": item})
    else:
        return None
