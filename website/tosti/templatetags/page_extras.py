from django import template
from django.apps import apps
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def render_page_extras(context):
    """
    Render HTML that apps want to add to every page (e.g. site-wide popups).

    Apps register this by defining ``page_extras(self, request)`` on their AppConfig, returning a list of
    already-rendered (and escaped) HTML strings. Templates can opt out by overriding ``{% block page_extras %}``.
    """
    request = context.get("request")
    if request is None:
        return ""

    extras = []
    for app in apps.get_app_configs():
        if hasattr(app, "page_extras"):
            extras += app.page_extras(request)
    return mark_safe("\n".join(extras))
