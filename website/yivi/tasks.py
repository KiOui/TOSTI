from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from yivi import models


@shared_task
def yivi_cleanup_sessions():
    """Cleanup sessions."""
    cleanup_before_date = timezone.now() - timedelta(days=1)
    models.Session.objects.filter(created_at__lt=cleanup_before_date).delete()
