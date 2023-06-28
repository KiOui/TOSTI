from django.contrib.auth import get_user_model
from django.core.signing import BadSignature, SignatureExpired
from django.test import TestCase

from users.services import get_identification_token, get_user_from_identification_token

User = get_user_model()


class IdentificationTokenTest(TestCase):
    """Test identification tokens."""

    def setUp(self):
        """Set up the test case."""
        self.user = User.objects.create_user(username="test", password="test")

    def test_identification_tokens(self):
        token = get_identification_token(self.user)
        user = get_user_from_identification_token(token)
        self.assertEqual(user, self.user)

        with self.assertRaises(BadSignature):
            get_user_from_identification_token(token + "a")

        with self.assertRaises(SignatureExpired):
            get_user_from_identification_token(token, max_age=0)
