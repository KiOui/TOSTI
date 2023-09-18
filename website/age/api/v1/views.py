from rest_framework.response import Response
from rest_framework.views import APIView

from age.services import get_yivi_client
from age.yivi import YiviException
from tosti.api.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class YiviStartAPIView(APIView):
    """
    Yivi Start API View.

    Use this endpoint to start a Yivi session.
    """

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "POST": ["write"],
    }

    def post(self, request, **kwargs):
        """Start a Yivi request."""
        yivi_client = get_yivi_client()
        try:
            response = yivi_client.start_session(
                {
                    "@context": "https://irma.app/ld/request/disclosure/v2",
                    "disclose": [[["irma-demo.MijnOverheid.ageLower.over18"]]],
                }
            )
            return Response(data=response)
        except YiviException as e:
            return Response(status=e.http_status, data=e.msg)


class YiviResultAPIView(APIView):
    """
    Yivi Result API View.

    Use this endpoint to get the result of a Yivi session.
    """

    permission_classes = [IsAuthenticatedOrTokenHasScopeForMethod]
    required_scopes_for_method = {
        "GET": ["write"],
    }

    def get(self, request, **kwargs):
        """Get the result of a Yivi session."""
        yivi_client = get_yivi_client()
        try:
            return Response(data=yivi_client.session_status(""))
        except YiviException as e:
            return Response(status=e.http_status, data=e.msg)
