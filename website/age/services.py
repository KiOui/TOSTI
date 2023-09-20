from django.conf import settings
from django.contrib.auth import get_user_model

from age import models

User = get_user_model()


def verify_minimum_age(user: User, minimum_age: int = 18) -> bool:
    """Verify whether someone has a certain minimum age."""
    minimum_registered_age = get_minimum_age(user)
    return minimum_registered_age is not None and minimum_registered_age >= minimum_age


def get_minimum_age(user: User):
    """Get the minimum age of a user."""
    try:
        age_registration = models.AgeRegistration.objects.get(user=user)
    except models.AgeRegistration.DoesNotExist:
        return None
    return age_registration.minimum_age


def construct_disclose_tree(user: User):
    """Construct the disclose tree."""
    yivi_disclose_tree = []
    yivi_age_disclose_tree = []
    for yivi_key in settings.AGE_VERIFICATION_MINIMUM_AGE_MAPPING.keys():
        yivi_age_disclose_tree.append([yivi_key])

    yivi_disclose_tree.append(yivi_age_disclose_tree)
    if settings.AGE_VERIFICATION_USERNAME_ATTRIBUTE is not None:
        yivi_disclose_tree.append(
            [
                [
                    {"type": settings.AGE_VERIFICATION_USERNAME_ATTRIBUTE, "value": user.username},
                    {
                        "type": settings.AGE_VERIFICATION_INSTITUTE_ATTRIBUTE,
                        "value": settings.AGE_VERIFICATION_INSTITUTE_VALUE,
                    },
                ]
            ]
        )

    return yivi_disclose_tree


def get_proven_attributes_from_proof_tree(proof_tree):
    """Get the proven attributes from a proof tree."""
    proven_attributes = []
    for attribute_conjuction_clause in proof_tree:
        for possibly_proven_attribute in attribute_conjuction_clause:
            if possibly_proven_attribute["status"] == "PRESENT":
                proven_attributes.append(possibly_proven_attribute)
    return proven_attributes


def get_highest_proven_age_from_proven_attributes(proven_attributes):
    """Get the highest minimum age from the proven attributes."""
    highest_age = None
    for proven_attribute in proven_attributes:
        proven_attribute_id = proven_attribute["id"]
        if proven_attribute_id in settings.AGE_VERIFICATION_MINIMUM_AGE_MAPPING.keys():
            proven_attribute_minimum_age = settings.AGE_VERIFICATION_MINIMUM_AGE_MAPPING[proven_attribute_id]
            if highest_age is None or highest_age < proven_attribute_minimum_age:
                highest_age = proven_attribute_minimum_age
    return highest_age


def get_username_from_proven_attributes(proven_attributes):
    """Get the username attribute value from a proof tree."""
    if settings.AGE_VERIFICATION_USERNAME_ATTRIBUTE is None:
        return None

    for proven_attribute in proven_attributes:
        proven_attribute_id = proven_attribute["id"]
        if proven_attribute_id == settings.AGE_VERIFICATION_USERNAME_ATTRIBUTE:
            return proven_attribute["rawvalue"]
    return None
