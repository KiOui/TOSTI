from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from tosti.api.openapi import CustomAutoSchema
from yivi import signals
from yivi.models import Session
from yivi.services import get_yivi_client
from yivi.yivi import YiviException
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
    schema = CustomAutoSchema(
        request_schema={
            "type": "object",
            "properties": {
                "disclose": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                },
            },
        },
        response_schema={
            "type": "object",
            "properties": {
                "sessionPtr": {
                    "type": "object",
                    "properties": {
                        "u": {"type": "string", "format": "url"},
                        "irmaqr": {"type": "string"},
                    },
                },
                "token": {"type": "string"},
                "frontendRequest": {
                    "type": "object",
                    "properties": {
                        "authorization": {"type": "string"},
                        "minProtocolVersion": {"type": "string"},
                        "maxProtocolVersion": {"type": "string"},
                    },
                },
            },
        },
    )

    def post(self, request, **kwargs):
        """Start a Yivi request."""
        yivi_client = get_yivi_client()
        disclose = request.data.get("disclose", None)
        if disclose is None:
            return Response(status=400, data="Parameter 'disclose' must be specified.")

        try:
            response = yivi_client.start_session(
                {
                    "@context": "https://irma.app/ld/request/disclosure/v2",
                    "disclose": disclose,
                }
            )
        except YiviException as e:
            return Response(status=e.http_status, data=e.msg)

        token = response["token"]
        session = Session.objects.create(session_token=token, user=request.user)
        response["token"] = session.id
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
    schema = CustomAutoSchema(
        response_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string"},
                "status": {"type": "string"},
                "type": {"type": "string"},
                "proofStatus": {"type": "string"},
                "disclosed": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rawvalue": {"type": "string"},
                                "value": {"type": "object", "properties": {"": {"type": "string"}}},
                                "id": {"type": "string"},
                                "status": {"type": "string"},
                                "issuancetime": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        },
    )

    def get(self, request, **kwargs):
        """Get the result of a Yivi session."""
        yivi_client = get_yivi_client()
        session_uuid = kwargs.get("pk")
        session = get_object_or_404(Session, pk=session_uuid, user=request.user)
        try:
            response = yivi_client.session_result(session.session_token)
        except YiviException as e:
            return Response(status=e.http_status, data=e.msg)

        response["token"] = session.id

        if response.get("proofStatus") == "VALID":
            signals.attributes_verified.send_robust(self.__class__, session=session, attributes=response["disclosed"])

        return Response(data=response)
