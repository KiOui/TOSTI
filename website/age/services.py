from django.conf import settings

from age.yivi import Yivi


def get_yivi_client() -> Yivi:
    """Get a Yivi Client."""
    return Yivi(settings.YIVI_SERVER, token=settings.YIVI_TOKEN)
