from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from sp.utils import login

User = get_user_model()


def post_login(request, user, idp, saml):
    """Log a user in to the system using a custom function."""
    update_staff_status(user)
    update_user_name(user)
    return login(request, user, idp, saml)


def update_user_name(user):
    """Update the user's first and last name based on their display name."""
    if user.full_name and not user.first_name and not user.last_name:
        first_name = user.full_name[user.full_name.find("(") + 1 : user.full_name.find(")")]  # noqa: E203
        last_name = user.full_name.split(",")[0]

        insert = user.full_name[user.full_name.rfind(".") + 1 : user.full_name.find("(")].strip()  # noqa: E203
        if len(insert) > 0:
            last_name = insert + " " + last_name

        user.first_name = first_name
        user.last_name = last_name
        user.save()


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
