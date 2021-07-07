import oauth2_provider.models
from django.conf import settings
from django.urls import path, include
from django.views.generic import TemplateView


def get_swagger_client_id():
    swagger_oauth_client, _ = oauth2_provider.models.Application.objects.get_or_create(
        name="Swagger",
        client_type=oauth2_provider.models.Application.CLIENT_PUBLIC,
        authorization_grant_type=oauth2_provider.models.Application.GRANT_IMPLICIT,
        redirect_uris=settings.SWAGGER_OAUTH_CALLBACK_URL,
    )
    return swagger_oauth_client.client_id


urlpatterns = [
    path(
        "",
        include(
            [
                path("v1/", include("tosti.api.v1.urls", namespace="v1")),
            ]
        ),
    ),  # noqa
    path(
        "docs",
        TemplateView.as_view(
            template_name="tosti/swagger.html",
            extra_context={"schema_urls": ["v1:schema-v1"], "swagger_oauth_client_id": get_swagger_client_id()},
        ),
        name="swagger",
    ),
    path(
        "docs/oauth2-redirect",
        TemplateView.as_view(template_name="tosti/swagger-oauth2-redirect.html"),
        name="swagger-oauth-redirect",
    ),
]
