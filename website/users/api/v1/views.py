from django.contrib.auth import get_user_model
from django.http import Http404
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from tosti.api.permissions import IsAuthenticatedOrTokenHasScopeForMethod
from users.api.v1.serializers import UserSerializer
from users.services import get_identification_token

User = get_user_model()


class MeRetrieveAPIView(RetrieveAPIView):
    """
    Me Retrieve API View.

    Permission required: read

    Use this API view to get details about the currently logged in User.
    """

    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["read"],
    }

    def get_object(self):
        """Get the current logged-in User."""
        try:
            return self.queryset.get(pk=self.request.user.pk)
        except User.DoesNotExist:
            raise Http404()


class IdentificationTokenView(APIView):
    """
    Identification Token View.

    Permission required: read

    Use this API view to get the identification token of the currently logged-in User.
    """

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["read"],
    }

    def get(self, request, *args, **kwargs):
        """Get the identification token of the currently logged in User."""
        user = request.user
        token = get_identification_token(user)
        return Response({"token": token})
