from django.contrib.auth import get_user_model
from django.core.signing import SignatureExpired, BadSignature
from oauth2_provider.views.mixins import ClientProtectedResourceMixin
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from fridges.services import user_can_open_fridge, log_access
from users.services import get_user_from_identification_token

User = get_user_model()


class FridgeUnlockAPIView(ClientProtectedResourceMixin, APIView):
    """API view for testing whether a Fridge is allowed to be unlocked."""

    def post(self, request, *args, **kwargs):
        """
        Process a request to unlock.
        """
        fridge_candidates = request.auth.application.fridges.all()

        if fridge_candidates.count() == 0:
            return Response(
                {"detail": "No fridges available"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_token = request.data.get("user_token", None)
        if user_token is None:
            return Response(
                {"detail": "Missing user_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = get_user_from_identification_token(user_token)
        except (User.DoesNotExist, BadSignature, SignatureExpired):
            return Response(
                {"detail": "Invalid user_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = []
        for fridge in fridge_candidates:
            user_can_open, how_long = user_can_open_fridge(user, fridge)
            if user_can_open:
                log_access(user, fridge)
                response.append({"fridge": fridge.slug, "unlock_for": how_long})

        return Response(
            {"user": user.username, "unlock": response},
            status=status.HTTP_200_OK,
        )
