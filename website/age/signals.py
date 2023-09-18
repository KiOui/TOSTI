from django.conf import settings
from django.dispatch import receiver

from age import models
from yivi.models import Session
from yivi.signals import attributes_verified


@receiver(attributes_verified)
def update_is_over_18(sender, **kwargs):
    session: Session = kwargs.get("session")
    if session.user is None or models.Is18YearsOld.objects.filter(user=session.user).exists():
        return

    attributes = kwargs.get("attributes")
    for attribute_conjuction_clause in attributes:
        for attribute_disjunction_clause in attribute_conjuction_clause:
            attribute_id = attribute_disjunction_clause["id"]
            if (
                attribute_id == settings.AGE_VERIFICATION_DISCLOSE_ATTRIBUTE
                and attribute_disjunction_clause["status"] == "PRESENT"
            ):
                models.Is18YearsOld.objects.create(user=session.user)
