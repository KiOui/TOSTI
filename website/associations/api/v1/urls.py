from django.urls import path, register_converter
from associations.api.v1.views import AssociationListAPIView
from associations.converters import AssociationConverter

register_converter(AssociationConverter, "association")

urlpatterns = [
    path("", AssociationListAPIView.as_view(), name="association_list"),
]
