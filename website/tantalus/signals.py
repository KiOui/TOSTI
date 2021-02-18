import logging

import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from orders.models import Shift


@receiver(post_save, sender=Shift)
def sync_to_tantalus(sender, instance, **kwargs):
    """Synchronize Orders to Tantalus if a Shift is made finalized."""
    s = requests.session()

    r = s.post(settings.TANTALUS_ENDPOINT_URL + "login", json={"username": settings.TANTALUS_USERNAME, "password": settings.TANTALUS_PASSWORD})
    try:
        r.raise_for_status()
        r = s.get(settings.TANTALUS_ENDPOINT_URL + "products")
        r.raise_for_status()
        print(r.text)
    except requests.HTTPError as e:
        logging.error("Tantalus synchronization failed with the following exception: {}".format(e))
