from django.shortcuts import render, redirect
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Index view."""

    template_name = "tosti/index.html"

    def get(self, request, **kwargs):
        """
        GET request for IndexView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the index page
        """
        return render(request, self.template_name)


class PrivacyView(TemplateView):
    """Privacy policy view."""

    template_name = "tosti/privacy.html"


class WelcomeView(TemplateView):
    """Welcome page."""

    template_name = "tosti/welcome.html"


def handler403(request, exception):
    """
    Handle a 403 (permission denied) exception.

    :param request: the request
    :param exception: the exception
    :return: a render of the 403 page
    """
    if request.user.is_authenticated:
        return render(request, "tosti/403.html", status=403)
    else:
        return redirect("users:login")


def handler404(request, exception):
    """
    Handle a 404 (page not found) exception.

    :param request: the request
    :param exception: the exception
    :return: a render of the 404 page
    """
    return render(request, "tosti/404.html", status=404)


def handler500(request):
    """
    Handle a 50x (server fault) exception.

    :param request: the request
    :return: a render of the 500 page
    """
    return render(request, "tosti/500.html", status=500)
