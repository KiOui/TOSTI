from django.apps import AppConfig


def user_has_borrel_brevet_lazy(request):
    """Check if user has borrel brevet (but only import the model on execution)."""
    from qualifications.models import BasicBorrelBrevet

    try:
        _ = request.user.basic_borrel_brevet
    except BasicBorrelBrevet.DoesNotExist:
        return False
    except AttributeError:  # for AnonymousUser
        return False
    return True


class QualificationsConfig(AppConfig):
    """Qualifications config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "qualifications"
