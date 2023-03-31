from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SilvasoftServicesTests(TestCase):
    fixtures = ["users.json", "associations.json", "borrel.json", "silvasoft.json"]
