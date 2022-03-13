from rest_framework import filters
from rest_framework.generics import ListAPIView
from associations.models import Association
from .serializers import AssociationSerializer


class AssociationListAPIView(ListAPIView):
    """
    Association List API View.

    Permissions required: None

    Use this endpoint to get a list of all associations.
    """

    serializer_class = AssociationSerializer
    queryset = Association.objects.all()
    filter_backends = (
        filters.SearchFilter,
    )
    search_fields = ["name"]
