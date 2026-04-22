import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tosti.settings")

app = Celery("tosti", result_extended=True)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
