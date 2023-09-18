from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from age.models import SessionMapping
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
        except YiviException as e:
            return Response(status=e.http_status, data=e.msg)

        token = response["token"]
        session_mapping = SessionMapping.objects.create(session_token=token)
        response["token"] = session_mapping.id
        return Response(data=response)


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
        session_uuid = kwargs.get("pk")
        session = get_object_or_404(SessionMapping, pk=session_uuid)
        try:
            return Response(data=yivi_client.session_result(session.session_token))
        except YiviException as e:
            return Response(status=e.http_status, data=e.msg)
