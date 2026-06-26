from csp.decorators import csp_update
from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from .oauth_discovery import (
    DynamicClientRegistrationView,
    GranularAuthorizationView,
    OAuthAuthorizationServerMetadataView,
    OAuthProtectedResourceMetadataView,
)
from .views import (
    IndexView,
    PrivacyView,
    handler403 as custom_handler403,
    handler404 as custom_handler404,
    handler500 as custom_handler500,
    DocumentationView,
    ExplainerView,
    MCPToolsDocsView,
    OAuthIntegrationDocsView,
    AfterLoginRedirectView,
    LogoutView,
    StatisticsView,
)

# The OAuth consent screen POSTs back to /oauth/authorize/ which then 302s
# to the client's redirect_uri (a third-party origin by design). Browsers
# treat the post-form-submit redirect as a form-action target, so the
# global ``form-action: 'self'`` would break the flow. Loosen the directive
# for this single view, not site-wide.
authorize_view = csp_update({"form-action": ["https:"]})(
    GranularAuthorizationView.as_view()
)

handler403 = custom_handler403
handler404 = custom_handler404
handler500 = custom_handler500

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("", include("mcp_server.urls")),
    path("mcp/docs/", MCPToolsDocsView.as_view(), name="mcp-tools-docs"),
    path(
        ".well-known/oauth-authorization-server",
        OAuthAuthorizationServerMetadataView.as_view(),
        name="oauth-authorization-server-metadata",
    ),
    path(
        ".well-known/oauth-protected-resource",
        OAuthProtectedResourceMetadataView.as_view(),
        name="oauth-protected-resource-metadata",
    ),
    path(
        "oauth/register/",
        DynamicClientRegistrationView.as_view(),
        name="oauth-dynamic-client-registration",
    ),
    path(
        "oauth/docs/",
        OAuthIntegrationDocsView.as_view(),
        name="oauth-integration-docs",
    ),
    # Must shadow the upstream pattern (defined inside the include below) so
    # the per-view CSP override applies. Same name & namespace as upstream so
    # ``reverse('oauth2_provider:authorize')`` still works everywhere.
    path(
        "oauth/authorize/",
        authorize_view,
        name="authorize",
    ),
    path("oauth/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("documentation/", DocumentationView.as_view(), name="documentation"),
    path("explainers/", ExplainerView.as_view(), name="explainers"),
    path("statistics/", StatisticsView.as_view(), name="statistics"),
    path(
        "users/",
        include(("users.urls", "users"), namespace="users"),
    ),
    path(
        "venues/",
        include(("venues.urls", "venues"), namespace="venues"),
    ),
    path(
        "borrel/",
        include(("borrel.urls", "borrel"), namespace="borrel"),
    ),
    path(
        "shifts/",
        include(("orders.urls", "orders"), namespace="orders"),
    ),
    path(
        "thaliedje/",
        include(("thaliedje.urls", "thaliedje"), namespace="thaliedje"),
    ),
    path(
        "tampon/",
        include(("tampon.urls", "tampon"), namespace="tampon"),
    ),
    path(
        "fridges/",
        include(("fridges.urls", "fridges"), namespace="fridges"),
    ),
    path(
        "status/",
        include(("status_screen.urls", "status_screen"), namespace="status_screen"),
    ),
    path("api/", include("tosti.api.urls")),
    path("saml/", include("djangosaml2.urls")),
    path(
        "sso/science/", include("djangosaml2.urls")
    ),  # Legacy for as long as CNCZ IDP isn't updated to use the new URL
    path(
        "sso/science/slo/",
        RedirectView.as_view(url="/sso/science/ls/", query_string=True),
        name="slo_legacy_redirect",
    ),  # Legacy for as long as CNCZ IDP isn't updated to use the new URL
    path(
        "login/",
        RedirectView.as_view(
            url="/saml/login/" if not settings.DEBUG else "/admin-login",
            query_string=True,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "admin/login/",
        RedirectView.as_view(url="/login", query_string=True),
        name="login-redirect",
    ),
    path("admin-login/", admin.site.login, name="admin-login"),
    path("admin-logout/", admin.site.logout, name="admin-logout"),
    path("after-login/", AfterLoginRedirectView.as_view(), name="after-login"),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path(
        "robots.txt",
        RedirectView.as_view(url=static("tosti/robots.txt"), permanent=True),
        name="robots-txt",
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(url=static("tosti/favicon/favicon.ico"), permanent=True),
        name="favicon",
    ),
    path(
        "apple-touch-icon.png",
        RedirectView.as_view(
            url=static("tosti/favicon/apple-touch-icon.png"), permanent=True
        ),
    ),
    path(
        "apple-touch-icon-precomposed.png",
        RedirectView.as_view(
            url=static("tosti/favicon/apple-touch-icon.png"), permanent=True
        ),
    ),
    path(
        "apple-touch-icon-120x120.png",
        RedirectView.as_view(
            url=static("tosti/favicon/apple-touch-icon.png"), permanent=True
        ),
    ),
    path(
        "apple-touch-icon-120x120-precomposed.png",
        RedirectView.as_view(
            url=static("tosti/favicon/apple-touch-icon.png"), permanent=True
        ),
    ),
    path(
        "android-chrome-192x192.png",
        RedirectView.as_view(
            url=static("tosti/favicon/android-chrome-192x192.png"), permanent=True
        ),
    ),
    path(
        "android-chrome-512x512.png",
        RedirectView.as_view(
            url=static("tosti/favicon/android-chrome-512x512.png"), permanent=True
        ),
    ),
]
