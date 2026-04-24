from django.conf import settings

from yivi.yivi import Yivi, YiviException


def get_yivi_client() -> Yivi:
    """Get a Yivi Client."""
    if not settings.YIVI_SERVER_URL:
        raise YiviException(
            http_status=503,
            code="yivi_not_configured",
            msg="Yivi server is not configured.",
        )
    return Yivi(settings.YIVI_SERVER_URL, token=settings.YIVI_SERVER_TOKEN)
