from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Static landing page for T.A.M.P.O.N."""

    template_name = "tampon/index.html"
