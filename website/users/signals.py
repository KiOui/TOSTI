from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .services import join_auto_join_groups

User = get_user_model()


@receiver(post_save, sender=User)
def join_autojoin_groups(sender, instance, created, **kwargs):
    """Makes a User join the auto-join-groups whenever a User is created."""
    if created:
        join_auto_join_groups(instance)
