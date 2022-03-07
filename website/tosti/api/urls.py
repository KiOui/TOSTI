import itertools

import oauth2_provider.models
from django.conf import settings
from django.urls import path, include
from django.views.generic import TemplateView


def get_swagger_client_id():
    """Get the client_id for a Swagger OAuth2 application."""

    hosts = settings.ALLOWED_HOSTS
    if not hosts:
        hosts = ["localhost", "127.0.0.1"]
    redirect_uris = " ".join(
        [
            f"{scheme}://{url}/api/docs/oauth2-redirect"
            for scheme, url in itertools.product(settings.OAUTH2_PROVIDER["ALLOWED_REDIRECT_URI_SCHEMES"], hosts)
        ]
    )

    swagger_oauth_client, _ = oauth2_provider.models.Application.objects.get_or_create(
        name="Swagger",
    )
    swagger_oauth_client.client_type = oauth2_provider.models.Application.CLIENT_PUBLIC
    swagger_oauth_client.authorization_grant_type = oauth2_provider.models.Application.GRANT_IMPLICIT
    swagger_oauth_client.redirect_uris = redirect_uris
    swagger_oauth_client.save()
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
            extra_context={"schema_urls": ["v1:schema-v1"], "swagger_oauth_client_id": get_swagger_client_id},
        ),
        name="swagger",
    ),
    path(
        "docs/oauth2-redirect",
        TemplateView.as_view(template_name="tosti/swagger-oauth2-redirect.html"),
        name="swagger-oauth-redirect",
    ),
]
