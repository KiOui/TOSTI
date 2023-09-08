from django.db.models import Q

from fridges.models import AccessLog


def user_is_blacklisted(user, fridge):
    """Return whether a user is blacklisted from opening a fridge."""
    return fridge.blacklist.filter(user=user).exists()


def user_can_open_fridge(user, fridge):
    """Return whether a user can open a fridge, and for how long."""
    if user.has_perm("fridges.open_always", fridge):
        return True, fridge.unlock_for_how_long

    if not fridge.is_active:
        return False, None

    if user_is_blacklisted(user, fridge):
        return False, None

    opening_hours = fridge.current_opening_hours

    if not opening_hours.exists():
        return False, None

    if opening_hours.filter(Q(restrict_to_groups__in=user.groups.all()) | Q(restrict_to_groups__isnull=True)).exists():
        return True, fridge.unlock_for_how_long

    return False, None


def log_access(user, fridge):
    """Log a user opening a fridge."""
    AccessLog.objects.create(user=user, fridge=fridge)
