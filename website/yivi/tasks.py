from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from tosti.metrics import emit as emit_metric
from yivi import models


@shared_task
def yivi_cleanup_sessions():
    """Cleanup sessions."""
    cleanup_before_date = timezone.now() - timedelta(days=1)
    deleted, _ = models.Session.objects.filter(
        created_at__lt=cleanup_before_date
    ).delete()
    emit_metric("cron_yivi_cleanup_sessions_run", deleted=deleted)
