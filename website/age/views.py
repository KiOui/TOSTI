import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from age import models
from age.services import verify_minimum_age, construct_disclose_tree


class AgeOverviewView(LoginRequiredMixin, TemplateView):
    """Age Overview View."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """Get Age Overview View."""

        is_18_years_old = verify_minimum_age(request.user)
        rendered_tab = render_to_string(
            "age/age_overview.html",
            context={
                "is_over_18": is_18_years_old,
                "disclose": mark_safe(json.dumps({"disclose": construct_disclose_tree()})),
            },
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
