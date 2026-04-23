from celery import shared_task

from tosti.services import data_minimisation


@shared_task
def tosti_data_minimisation():
    """Minimise data in the database."""
    data_minimisation(dry_run=False)
