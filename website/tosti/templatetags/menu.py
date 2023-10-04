from django import template
from django.apps import apps

register = template.Library()


def collect_menu_items(request):
    menu_items = []
    for app in apps.get_app_configs():
        if hasattr(app, "menu_items"):
            app_menu_items = app.menu_items(request)
            menu_items += app_menu_items
    return menu_items


@register.inclusion_tag("tosti/menu/main_menu_items.html", takes_context=True)
def render_main_menu_start(context):
    menu = collect_menu_items(context.get("request"))
    menu = filter(lambda x: x["location"] == "start", menu)
    menu = sorted(menu, key=lambda x: x["order"])
    return {"menu": menu}


@register.inclusion_tag("tosti/menu/main_menu_items.html", takes_context=True)
def render_main_menu_end(context):
    menu = collect_menu_items(context.get("request"))
    menu = filter(lambda x: x["location"] == "end", menu)
    menu = sorted(menu, key=lambda x: x["order"])
    return {"menu": menu}


@register.inclusion_tag("tosti/menu/user_menu_items.html", takes_context=True)
def render_user_menu(context):
    menu = collect_menu_items(context.get("request"))
    menu = filter(lambda x: x["location"] == "user", menu)
    menu = sorted(menu, key=lambda x: x["order"])
    return {"menu": menu}
