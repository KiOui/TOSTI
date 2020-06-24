from django.conf import settings  # import the settings file


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
