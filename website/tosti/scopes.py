"""OAuth2 scopes backend for TOSTI.

django-oauth-toolkit's default ``SettingsScopes`` treats every scope in
``OAUTH2_PROVIDER["SCOPES"]`` as available to every application, which means a
dynamically-registered MCP client can request the same scopes as a
maintainer-provisioned confidential client. TOSTI splits the two:

  - **Public scopes** are advertised in the RFC 8414 discovery document and
    can be requested by any application, including
    :attr:`Application.RegistrationSource.DCR` clients that self-registered
    over the public DCR endpoint.
  - **Restricted scopes** are reserved for applications provisioned out of
    band by a maintainer (``registration_source="manual"``). They are still
    published in :meth:`get_all_scopes` so admin UIs list them, but are
    filtered out of discovery *and* rejected at authorization time when the
    requesting application is DCR-created.

Configure via ``OAUTH2_PROVIDER["RESTRICTED_SCOPES"]`` — a list of scope names
present in ``SCOPES`` that should be treated as maintainer-only. Scopes not in
that list are public by default.
"""

from django.conf import settings
from oauth2_provider.models import get_application_model
from oauth2_provider.scopes import BaseScopes


def _restricted_scopes() -> set[str]:
    """Names of the scopes reserved for manually-provisioned applications."""
    return set(settings.OAUTH2_PROVIDER.get("RESTRICTED_SCOPES", []))


def _is_dcr_application(application) -> bool:
    """Whether *application* self-registered via RFC 7591 DCR.

    Anything else — manually provisioned in the admin, or provisioned via a
    future federation mechanism — is trusted with restricted scopes.
    """
    if application is None:
        return True  # unknown audience → treat as public / most restrictive
    Application = get_application_model()
    return application.registration_source == Application.RegistrationSource.DCR


class TostiScopes(BaseScopes):
    """Scopes backend that gates restricted scopes on registration source."""

    def get_all_scopes(self):
        return settings.OAUTH2_PROVIDER["SCOPES"]

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        all_scopes = list(self.get_all_scopes().keys())
        if _is_dcr_application(application):
            restricted = _restricted_scopes()
            return [s for s in all_scopes if s not in restricted]
        return all_scopes

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        # Match SettingsScopes' default: ``read`` is the safe zero-scope baseline
        # the library falls back to when a client omits ``scope`` entirely.
        return ["read"]
