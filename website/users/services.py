from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.db.models import Count, ProtectedError
from django.utils import timezone

from associations.models import Association

User = get_user_model()


def get_identification_token(user):
    """Get the identification token for a user."""
    signer = TimestampSigner()
    token = signer.sign(user.username)
    return token


def verify_identification_token(token: str, max_age=900) -> (bool, str):
    """Verify an identification token."""
    signer = TimestampSigner()
    try:
        return True, signer.unsign(token, max_age=max_age)
    except SignatureExpired:
        return False, None
    except BadSignature:
        return False, None


def get_user_from_identification_token(token, max_age=timedelta(seconds=20)):
    """
    Get the user from an identification token.

    :param token: identification token
    :param max_age: maximum age of the token (in seconds or timedelta, default 20 seconds)
    :return: the user
    :raises SignatureExpired: if the token is expired
    :raises BadSignature: if the token is invalid
    :raises User.DoesNotExist: if the user does not exist
    """
    signer = TimestampSigner()
    username = signer.unsign(token, max_age=max_age)
    user = User.objects.get(username=username)
    return user


def update_staff_status(user):
    """Update the is_staff value of a user."""
    if len(user.groups.all().filter(settings__gets_staff_permissions=True)) > 0:
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
            try:
                if not dry_run:
                    user.delete()
                processed.append(user)
            except ProtectedError:
                # Skip users with protected references
                continue
    return processed


def generate_users_per_association():
    """Generate statistics about users per association."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    for association in Association.objects.annotate(user_amount=Count("users")):
        data["labels"].append(str(association))
        data["datasets"][0]["data"].append(association.user_amount)

    return data
