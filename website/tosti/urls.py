from csp.decorators import csp_update
from django.conf import settings
from django.contrib import admin
from django.templatetags.static import static
from django.urls import path, include
from django.views.generic import RedirectView

from oauth2_provider.urls import (
    base_urlpatterns as oauth2_base_urlpatterns,
    dcr_urlpatterns as oauth2_dcr_urlpatterns,
    management_urlpatterns as oauth2_management_urlpatterns,
    metadata_urlpatterns as oauth2_metadata_urlpatterns,
    oidc_urlpatterns as oauth2_oidc_urlpatterns,
)

from .oauth_discovery import DCRLandingView, GranularAuthorizationView
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

# Compose the /oauth/ subpatterns from the library's parts, excluding
# ``metadata_urlpatterns`` which we mount separately at the server root (RFC
# 8414 requires the well-known URI at the origin root). Keeping the metadata
# names *only* in the root mount ensures the library's
# ``oauth2_authorization_server_issuer`` reverse (used by RFC 9207) produces
# the correct issuer (``https://host``, not ``https://host/oauth``).
oauth2_prefixed_urlpatterns = (
    oauth2_base_urlpatterns
    + oauth2_management_urlpatterns
    + oauth2_oidc_urlpatterns
    + oauth2_dcr_urlpatterns
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
    # RFC 8414 / RFC 9728 well-known documents MUST live at the origin root, not
    # under the /oauth/ prefix. Mounted as an anonymous list so the
    # ``oauth2_provider:oauth-server-metadata`` namespace remains associated
    # exclusively with the /oauth/ include below (a duplicate namespace would
    # break reverse-with-namespace). The library defers to ``OIDC_ISS_ENDPOINT``
    # for its issuer/authorization_servers derivation (set in settings), so
    # nothing else needs to reverse these names — the concrete /.well-known/…
    # URLs are all that clients need.
    path("", include(oauth2_metadata_urlpatterns)),
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
    # Shadow the upstream /register/ pattern with our HTML-branching wrapper so
    # browser GETs get a friendly landing page. The wrapper delegates to the
    # library view for POSTs and JSON GETs.
    path(
        "oauth/register/",
        DCRLandingView.as_view(),
        name="oauth2_provider_dcr_register_landing",
    ),
    # Mount the non-metadata OAuth2 URL groups under /oauth/. Metadata is
    # already published at the origin root above; splitting the groups keeps
    # the ``oauth2_provider`` namespace populated with every name the library
    # expects to reverse.
    path(
        "oauth/",
        include(
            (oauth2_prefixed_urlpatterns, "oauth2_provider"),
            namespace="oauth2_provider",
        ),
    ),
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
