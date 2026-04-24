from django.db.models.signals import post_save
from django.dispatch import receiver

from tosti.metrics import emit as emit_metric
from transactions.models import Account


@receiver(post_save, sender=Account)
def on_account_created(sender, instance, created, **kwargs):
    """Emit a metric when a user account is created."""
    if created:
        emit_metric("account_created")
