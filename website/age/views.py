import json

from django.contrib.auth.mixins import LoginRequiredMixin
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from age.services import construct_disclose_tree, get_minimum_age


class AgeOverviewView(LoginRequiredMixin, TemplateView):
    """Age Overview View."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """Get Age Overview View."""
        minimum_registered_age = get_minimum_age(request.user)

        return_url = request.build_absolute_uri(request.get_full_path())
        url_parts = list(urlparse(return_url))
        query_parameters = dict(parse_qsl(url_parts[4]))
        query_parameters["return_from_yivi"] = "true"
        url_parts[4] = urlencode(query_parameters)
        return_url = urlunparse(url_parts)

        rendered_tab = render_to_string(
            "age/age_overview.html",
            context={
                "minimum_registered_age": minimum_registered_age,
                "disclose": mark_safe(
                    json.dumps(
                        {
                            "@context": "https://irma.app/ld/request/disclosure/v2",
                            "disclose": construct_disclose_tree(request.user),
                            "clientReturnUrl": return_url,
                        }
                    )
                ),
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


def explainer_page_how_to_verify_age_with_yivi(request, item):
    """Render the explainer how to verify age with Yivi."""
    if request.user.is_authenticated:
        return render_to_string(
            "age/explainer_age_verification.html",
            context={"request": request, "item": item},
        )
    else:
        return None
