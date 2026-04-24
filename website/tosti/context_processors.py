from constance import config

from age.services import get_minimum_age


def footer_credits(request):
    """Get the footer credits as string."""
    return {"FOOTER_CREDITS_TEXT": config.FOOTER_CREDITS_TEXT}


def minimum_registered_age(request):
    """Context processor to check if the user has a minimum registered age."""
    if not request.user.is_authenticated:
        return {"minimum_registered_age": False}

    age = get_minimum_age(request.user)
    return {"minimum_registered_age": age is not None}
