"""
Shared helpers for MCP toolsets.

Each app contributes its own ``mcp.py`` defining a subclass of
``mcp_server.MCPToolset``. The ``mcp_server`` package autodiscovers them at
startup. Use ``require_scope`` here to gate write tools on an OAuth2 scope,
mirroring DRF's ``IsAuthenticatedOrTokenHasScope``.

To classify tools for the MCP UI (read-only vs destructive, etc.), set a
``tool_annotations`` class attribute on the toolset:

    class MyTools(MCPToolset):
        tool_annotations = {
            "list_things": {"readOnlyHint": True, "openWorldHint": False},
            "create_thing": {"readOnlyHint": False, "destructiveHint": False},
        }

These are stamped onto the registered tools in ``TostiConfig.ready`` so
they reach the client in the ``tools/list`` response. Clients (e.g. Claude
Desktop) use them to group tools into "Read" and "Write" sections and to
require user confirmation for destructive actions.
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


SERVER_INSTRUCTIONS = """\
TOSTI is the order/reservation/music system for the Huygens-building \
canteens at Radboud University. You're acting on behalf of an authenticated \
TOSTI user; everything you do is attributed to them and uses their \
permissions.

Tool conventions:

- Venues are identified by ``slug`` (e.g. ``noordkantine``, ``zuidkantine``). \
Resolve unknown venue references with ``list_venues`` first; never invent \
slugs.
- Shifts are identified by their integer ``id``. List active shifts with \
``list_active_shifts`` before placing an order; only shifts whose ``can_order`` \
is true accept new orders.
- Music tools target a specific venue's player. The same venue may be backed \
by Spotify or Marietje; the protocol abstracts over both — you don't need to \
care which.

Safety rules:

- Confirm with the user before invoking any tool that places an order, \
requests a song, or creates a reservation. These actions cost money, time, \
or social capital and are visible to other people.
- If a tool returns ``{"error": ...}``, surface the error to the user \
verbatim — do not retry with different arguments unless they explicitly ask.
- If you need a permission the user has not granted (an OAuth scope), the \
tool will return an error mentioning the scope. Ask the user to re-authorise \
TOSTI with that scope; do not work around it.

If a tool is not listed by ``tools/list``, it does not exist — do not \
invent one.\
"""


def stamp_tool_annotations():
    """Set MCP ``ToolAnnotations`` on every registered tool.

    Walks the global server's tool manager, recovers the originating
    ``MCPToolset`` class from ``tool.fn.class_``, and copies the matching
    entry from the class's ``tool_annotations`` dict onto the tool. Tools
    without an entry are left untouched (clients will treat them as
    "other" / unclassified).

    Called from ``TostiConfig.ready`` after Django's app registry is
    ready, so the tools are guaranteed to be in the manager.
    """
    from mcp.types import ToolAnnotations
    from mcp_server import mcp_server as global_mcp_server

    for tool in global_mcp_server._tool_manager.list_tools():
        caller = getattr(tool, "fn", None)
        toolset_cls = getattr(caller, "class_", None)
        if toolset_cls is None:
            continue
        annotations = getattr(toolset_cls, "tool_annotations", {}).get(tool.name)
        if not annotations:
            continue
        tool.annotations = ToolAnnotations(**annotations)
