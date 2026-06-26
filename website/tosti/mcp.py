"""
Shared helpers for MCP toolsets.

Each app contributes its own ``mcp.py`` defining a subclass of
``mcp_server.MCPToolset``. The ``mcp_server`` package autodiscovers them at
startup. Use ``require_scope`` here to gate write tools on an OAuth2 scope,
mirroring DRF's ``IsAuthenticatedOrTokenHasScope``.
"""


def require_scope(request, scope: str) -> str | None:
    """Return an error message if the request's bearer token lacks ``scope``.

    Session-authed users (no token) bypass scope checks just like the DRF
    ``IsAuthenticatedOrTokenHasScope`` permission. Returns ``None`` on success.
    """
    token = getattr(request, "auth", None)
    if token is None:
        return None  # Session auth → no scope check.
    if not hasattr(token, "is_valid") or not token.is_valid([scope]):
        return f"This tool requires the '{scope}' OAuth2 scope."
    return None
