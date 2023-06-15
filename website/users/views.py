from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.contrib.auth.models import Group

from tosti.filter import Filter
from .forms import AccountForm


User = get_user_model()


class AccountView(TemplateView):
    """Account View."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """GET request for the Account view."""
        form = AccountForm(
            initial={
                "full_name": request.user.full_name,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "username": request.user.username,
                "email": request.user.email,
                "association": request.user.association,
            }
        )
        rendered_tab = render_to_string("users/user_profile_form.html", context={"form": form}, request=request)
        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": rendered_tab,
            },
        )

    def post(self, request, **kwargs):
        """
        POST request for the account view.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the account view
        """
        form = AccountForm(request.POST)
        if form.is_valid():
            request.user.association = form.cleaned_data.get("association")
            request.user.save()
            messages.add_message(self.request, messages.SUCCESS, "Your profile has been saved.")
        rendered_tab = render_to_string("users/user_profile_form.html", context={"form": form}, request=request)
        return render(
            request,
            self.template_name,
            {"active": kwargs.get("active"), "tabs": kwargs.get("tabs"), "rendered_tab": rendered_tab},
        )


class AccountFilterView(LoginRequiredMixin, TemplateView):
    """Account Filter view."""

    template_name = "users/account.html"

    user_data_tabs = Filter()

    DEFAULT_ACTIVE_TAB = "account"

    def dispatch_to_view(self, active_view, request, *args, **kwargs):
        """Dispatch to the correct view."""
        tabs = self.user_data_tabs.do_filter([])

        new_kwargs = {
            "active": active_view,
            "tabs": tabs,
        }
        new_kwargs.update(kwargs)

        for tab in tabs:
            if active_view == tab["slug"]:
                return tab["view"](request, *args, **new_kwargs)
        return HttpResponseNotFound()

    def get(self, request, **kwargs):
        """Dispatch a request by picking the correct subclass."""
        active = request.GET.get("active", self.DEFAULT_ACTIVE_TAB)
        return self.dispatch_to_view(active, request, **kwargs)

    def post(self, request, **kwargs):
        """Dispatch a request by picking the correct subclass."""
        active = request.POST.get("active", self.DEFAULT_ACTIVE_TAB)
        return self.dispatch_to_view(active, request, **kwargs)


class StaffView(LoginRequiredMixin, TemplateView):
    """Staff view."""

    template_name = "users/staff.html"

    def get(self, request, **kwargs):
        """GET request for the staff view."""
        groups = Group.objects.filter(settings__display_on_website=True)
        return render(request, self.template_name, {"groups": groups})
