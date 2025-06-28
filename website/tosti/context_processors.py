from constance import config
from django.conf import settings  # import the settings file

from age.services import get_minimum_age


def google_analytics(request):
    """
    Context processor for google analytics key.

    :param request: the request
    :return: the google analytics key if it is defined
    """
    try:
        return {"GOOGLE_ANALYTICS_KEY": settings.GOOGLE_ANALYTICS_KEY}
    except AttributeError:
        return {}


def footer_credits(request):
    """Get the footer credits as string."""
    return {"FOOTER_CREDITS_TEXT": config.FOOTER_CREDITS_TEXT}


def minimum_registered_age(request):
    """Context processor to check if the user has a minimum registered age."""
    if not request.user.is_authenticated:
        return {"minimum_registered_age": False}

    age = get_minimum_age(request.user)
    return {"minimum_registered_age": age is not None}
