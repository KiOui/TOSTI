from celery import shared_task

from tosti.metrics import emit as emit_metric
from tosti.services import data_minimisation


@shared_task
def tosti_data_minimisation():
    """Minimise data in the database."""
    counts = data_minimisation(dry_run=False)
    emit_metric(
        "cron_data_minimisation_run",
        orders_affected=counts["orders"],
        thaliedje_affected=counts["thaliedje"],
        users_affected=counts["users"],
    )
