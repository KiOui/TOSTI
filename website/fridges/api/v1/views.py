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
    def post(self, request, fridge):
        """
        Unlock a fridge.
        """

        if "fridge" not in request.auth.application.name.lower():
            return Response(
                {"detail": "Invalid application"},
                status=status.HTTP_400_BAD_REQUEST,
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

        user_can_open, how_long = user_can_open_fridge(user, fridge)

        if not user_can_open:
            return Response(
                {"detail": "User cannot open fridge"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_access(user, fridge)

        return Response(
            {"user": user.username, "unlock_for": how_long},
            status=status.HTTP_200_OK,
        )
