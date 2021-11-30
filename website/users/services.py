from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from sp.utils import login

User = get_user_model()


def post_login(request, user, idp, saml):
    """Log a user in to the system using a custom function."""
    update_staff_status(user)
    return login(request, user, idp, saml)


def join_auto_join_groups(user):
    """Let new users join groups that are set for auto-joining."""
    auto_join_groups = Group.objects.filter(groupsettings__is_auto_join_group=True)
    for group in auto_join_groups:
        user.groups.add(group)


def update_staff_status(user):
    """Update the is_staff value of a user."""
    if len(user.groups.all().filter(groupsettings__gets_staff_permissions=True)) > 0:
        user.is_staff = True
        user.save()
    elif not user.is_superuser and len(user.user_permissions.all()) == 0:
        user.is_staff = False
        user.save()


def execute_data_minimisation(dry_run=False):
    """
    Remove accounts for users that have not been used for longer than 365 days.

    :param dry_run: does not really remove data if True
    :return: list of users from who data is removed
    """
    delete_before = timezone.now() - timedelta(days=365)
    users = User.objects.filter(last_login__lte=delete_before)

    processed = []
    for user in users:
        if not user.is_superuser:
            processed.append(user)
            if not dry_run:
                user.delete()

    return processed
