from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from tosti.api.openapi import CustomAutoSchema
from transactions.api.v1.serializers import AccountSerializer
from transactions.models import Account
from users.services import verify_identification_token
from transactions.api.v1.serializers import TransactionSerializer


class AccountRetrieveAPIView(CreateAPIView):
    """
    Account Retrieve API View.

    Permissions required: None

    Use this endpoint to get the transaction details for a user by using a token.
    """

    schema = CustomAutoSchema(
        request_schema={"type": "object", "properties": {"token": {"type": "string", "example": "string"}}}
    )

    serializer_class = AccountSerializer
    queryset = Account.objects.all()

    def post(self, request, **kwargs):
        token = request.data.get("token", None)
        if token is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        valid, signed_material = verify_identification_token(token)
        if not valid:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            account = self.queryset.get(user__username=signed_material)
            return Response(status=status.HTTP_200_OK, data=self.serializer_class(account).data)
        except Account.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class TransactionCreateAPIView(CreateAPIView):
    """
    Account Retrieve API View.

    Permissions required: transactions.add_transaction

    Use this endpoint to add a Transaction to an Account.
    """

    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        """Add request user to validated data."""
        serializer.save(processor=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a Transaction."""
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not request.user.has_perm("transactions.add_transaction"):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return super(TransactionCreateAPIView, self).create(request, *args, **kwargs)
