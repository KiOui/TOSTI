from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from .views import (
    IndexView,
    PrivacyView,
    handler403 as custom_handler403,
    handler404 as custom_handler404,
    handler500 as custom_handler500,
    DocumentationView,
    ExplainerView,
    AfterLoginRedirectView,
)

handler403 = custom_handler403
handler404 = custom_handler404
handler500 = custom_handler500

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("oauth/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("documentation/", DocumentationView.as_view(), name="documentation"),
    path("explainers/", ExplainerView.as_view(), name="explainers"),
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
    path("api/", include("tosti.api.urls")),
    path("sso/<idp_slug>/", include("sp.urls")),
    path(
        "login/",
        RedirectView.as_view(url="/sso/science/login/" if not settings.DEBUG else "/admin-login", query_string=True),
        name="login",
    ),
    path(
        "logout/",
        RedirectView.as_view(url="/sso/science/logout/" if not settings.DEBUG else "/admin-logout", query_string=True),
        name="logout",
    ),
    path("admin/login/", RedirectView.as_view(url="/login", query_string=True), name="login-redirect"),
    path("admin/logout/", RedirectView.as_view(url="/logout", query_string=True), name="logout-redirect"),
    path("admin-login/", admin.site.login, name="admin-login"),
    path("admin-logout/", admin.site.logout, name="admin-logout"),
    path("after-login/", AfterLoginRedirectView.as_view(), name="after-login"),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
]
