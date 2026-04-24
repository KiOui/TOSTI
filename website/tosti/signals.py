from django.dispatch import receiver
from oauth2_provider.signals import app_authorized

from tosti.metrics import emit as emit_metric


@receiver(app_authorized)
def on_oauth_app_authorized(sender, request, token, **kwargs):
    """Emit a metric when an OAuth2 access token is issued."""
    emit_metric(
        "oauth_token_issued",
        application=str(token.application) if token.application_id else None,
        scopes=token.scope or None,
    )
