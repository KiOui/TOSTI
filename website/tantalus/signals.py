import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Shift, Order
from tantalus.models import TantalusProduct
from tantalus.services import sort_orders_by_product, get_tantalus_client, TantalusException


@receiver(post_save, sender=Shift)
def sync_to_tantalus(sender, instance, **kwargs):
    """Synchronize Orders to Tantalus if a Shift is made finalized."""
    if instance.finalized:
        logging.info("Starting synchronization with Tantalus for Shift {}".format(instance))
        try:
            tantalus_client = get_tantalus_client()
        except TantalusException as e:
            logging.error(
                "Synchronization for Shift {} failed due to an Exception when intitialising the Tantalus Client. The "
                "following Exception occurred: {}".format(instance, e)
            )
            return

        orders = Order.objects.filter(shift=instance)
        for product, order_list in sort_orders_by_product(orders).items():
            try:
                tantalus_product = TantalusProduct.objects.get(product=product)
                tantalus_client.register_order(tantalus_product, len(order_list))
            except TantalusProduct.DoesNotExist:
                logging.warning(
                    "Skipping Tantalus synchronization for Shift {} and Product {} as the Product is not connected"
                    "to any TantalusProduct.".format(instance, product)
                )
            except TantalusException as e:
                logging.error(
                    "Synchronization for Shift {} and Product {} failed with the following Exception: {}".format(
                        instance, product, e
                    )
                )
        logging.info("Synchronization with Tantalus for Shift {} ended".format(instance))
