from django.urls import path, include
from rest_framework.schemas import get_schema_view

from tosti.api.openapi import OAuthSchemaGenerator

app_name = "tosti"

urlpatterns = [
    path("", include("orders.api.v1.urls")),
    path("marietje/", include("marietje.api.v1.urls")),
    path(
        "schema",
        get_schema_view(
            title="API v1",
            url="/api/v1/",
            version=1,
            urlconf="tosti.api.v1.urls",
            generator_class=OAuthSchemaGenerator,
        ),
        name="schema-v1",
    ),
]
