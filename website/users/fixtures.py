import string
import random

from django.contrib.auth import get_user_model
from faker import Factory as FakerFactory

User = get_user_model()


def create_fixtures():
    """Create random users."""
    faker = FakerFactory.create("nl_NL")

    for _ in range(0, 50):
        profile = faker.profile()
        profile["password"] = "".join(
            random.choice(string.ascii_uppercase + string.digits) for _ in range(16)
        )
        username = faker.numerify(text="s#######")
        User.objects.create_user(
            username,
            email=profile["mail"],
            password=profile["password"],
            full_name=profile["name"],
            first_name=profile["name"].split()[0],
            last_name=" ".join(profile["name"].split()[1:]),
        )

