from django.dispatch import receiver

from age import models
from age.models import AgeRegistration
from age.services import (
    get_proven_attributes_from_proof_tree,
    get_highest_proven_age_from_proven_attributes,
)
from yivi.models import Session
from yivi.signals import attributes_verified


@receiver(attributes_verified)
def update_minimum_age_when_proven(sender, **kwargs):
    """Update the minimum age of someone when proven by Yivi."""
    session: Session = kwargs.get("session")
    if session.user is None:
        return

    attributes = kwargs.get("attributes")
    proven_attributes = get_proven_attributes_from_proof_tree(attributes)
    minimum_proven_age = get_highest_proven_age_from_proven_attributes(
        proven_attributes
    )

    if minimum_proven_age is None:
        return

    attributes_log = [
        {
            "id": attr["id"],
            "rawvalue": attr["rawvalue"],
            "issuancetime": attr["issuancetime"],
        }
        for attr in proven_attributes
    ]

    try:
        age_registration = models.AgeRegistration.objects.get(user=session.user)
    except models.AgeRegistration.DoesNotExist:
        models.AgeRegistration.objects.create(
            user=session.user,
            minimum_age=minimum_proven_age,
            verified_by=AgeRegistration.YIVI,
            attributes=attributes_log,
            verified_by_user=None,
        )
        return

    if age_registration.minimum_age < minimum_proven_age:
        age_registration.minimum_age = minimum_proven_age
        age_registration.verified_by = AgeRegistration.YIVI
        age_registration.attributes = attributes_log
        age_registration.verified_by_user = None
        age_registration.save()
