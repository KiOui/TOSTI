from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from users.models import GroupSettings
from users.services import update_staff_status
from django.contrib.auth.models import Group

User = get_user_model()


@receiver(post_save, sender=GroupSettings)
def after_group_change(sender, instance, **kwargs):
    """Update the is_staff value of all users when possibly the gets_staff_permission field has changed."""
    try:
        users = instance.group.user_set.all()
    except Group.DoesNotExist:
        return

    for user in users:
        update_staff_status(user)


@receiver(m2m_changed, sender=User.groups.through)
def after_user_groups_changed(sender, instance, **kwargs):
    """Update the is_staff value of the users when they are added to groups."""
    action = kwargs.get("action")
    if action == "post_add" or action == "post_remove":
        # This receiver gets triggered by both User and Group objects.
        if isinstance(instance, User):
            update_staff_status(instance)
        elif isinstance(instance, Group):
            for user in instance.user_set.all():
                update_staff_status(user)
