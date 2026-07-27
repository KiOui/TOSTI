"""DRF authentication classes for TOSTI's OAuth2-protected endpoints."""

from oauth2_provider.contrib.rest_framework import (
    OAuth2ProtectedResourceAuthentication,
)


class TostiOAuth2Authentication(OAuth2ProtectedResourceAuthentication):
    """OAuth2 auth that advertises TOSTI's RFC 9728 metadata document.

    django-oauth-toolkit derives the ``resource_metadata`` URL by reversing
    ``oauth2_provider:oauth-resource-metadata``. TOSTI mounts the RFC 9728
    well-known at the origin root without the ``oauth2_provider`` namespace
    (see ``tosti.urls``), so the reverse would return ``None`` and drop the
    parameter — hard-code the well-known path here so every 401 challenge
    carries the pointer MCP clients need for discovery.
    """

    www_authenticate_realm = "tosti"

    def get_resource_metadata_url(self, request):
        return request.build_absolute_uri("/.well-known/oauth-protected-resource")
