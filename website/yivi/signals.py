import django.dispatch
from django.dispatch import receiver

from tosti.metrics import emit as emit_metric

attributes_verified = django.dispatch.Signal()


@receiver(attributes_verified)
def on_attributes_verified(sender, session, attributes, **kwargs):
    """Emit a metric on a successful Yivi verification."""
    emit_metric("yivi_attributes_verified")
