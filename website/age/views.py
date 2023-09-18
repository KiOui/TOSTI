from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from age import models


class AgeOverviewView(LoginRequiredMixin, TemplateView):
    """Age Overview View."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """Get Age Overview View."""

        is_18_years_old = models.Is18YearsOld.objects.filter(user=request.user).exists()
        rendered_tab = render_to_string("age/age_overview.html", context={"is_over_18": is_18_years_old})

        return render(
            request,
            self.template_name,
            {"active": kwargs.get("active"), "tabs": kwargs.get("tabs"), "rendered_tab": rendered_tab},
        )
