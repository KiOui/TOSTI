from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from users.models import GroupSettings
from users.services import update_staff_status

User = get_user_model()


@receiver(post_save, sender=GroupSettings)
def after_group_change(sender, instance, **kwargs):
    """Update the is_staff value of all users when possibly the gets_staff_permission field has changed."""
    for user in instance.group.user_set.all():
        update_staff_status(user)


@receiver(m2m_changed, sender=User.groups.through)
def after_user_groups_changed(sender, instance, **kwargs):
    """Update the is_staff value of the users when they are added to groups."""
    action = kwargs.get("action")
    pk_set = kwargs.get("pk_set")
    if action == "post_add" or action == "post_remove":
        for user in User.objects.filter(pk__in=pk_set):
            update_staff_status(user)
