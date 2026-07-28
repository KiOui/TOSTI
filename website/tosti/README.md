# `tosti/` &mdash; shared infrastructure

The `tosti` app is the seam between the per-feature apps and the rest of the project. It contains no business logic of its own (no orders, no music, no fridges); it owns settings, base templates, cross-cutting helpers, and the OAuth/MCP plumbing every other app benefits from.

If you find yourself adding feature behaviour here, stop. Per [`CONTRIBUTING.md`](../../CONTRIBUTING.md), feature behaviour belongs in its own app.

## What's here

| Thing | File(s) | Notes |
| --- | --- | --- |
| Project settings | `settings/base.py` + `production.py` / `development.py` | `INSTALLED_APPS`, middleware, CSP, OAuth config, Sentry init, SAML config. |
| Base templates | `templates/tosti/base.html` etc. | The site chrome (navbar, footer, modals, QR popup). Feature apps extend `tosti/base.html`. |
| OAuth discovery + DCR | `oauth_discovery.py` | RFC 8414 / 9728 metadata endpoints, RFC 7591 dynamic client registration, the custom `AuthorizationView` with granular per-scope consent. |
| OAuth integration docs | `templates/tosti/oauth_integration.html` + `views.py:OAuthIntegrationDocsView` | The `/oauth/docs/` page. |
| MCP wiring | `mcp.py` | Shared `require_scope` helper, `SERVER_INSTRUCTIONS` block, `stamp_tool_annotations`. The actual MCP server is initialised in `apps.py:TostiConfig.ready()`. |
| MCP tools docs | `templates/tosti/mcp_tools.html` + `views.py:MCPToolsDocsView` | The `/mcp/docs/` page. Reads the live `mcp_server` registry at request time. |
| Middleware | `middleware.py` | `HealthCheckMiddleware` (short-circuits `/live` `/ready`), `RequestMetricsMiddleware` (Sentry metrics), `MCPLandingMiddleware` (browser-friendly `/mcp`), `WWWAuthenticateMiddleware` (RFC 9728 pointer for 401s). |
| Connected apps tab | `views.py:ConnectedAppsView` | Lets users see and revoke the OAuth clients they've granted access to. |
| API credentials tab | `views.py:OAuthCredentialsRequestView` | Lets developers create their own OAuth applications. |
| Explainers framework | `templates/tosti/explainers.html` + `views.py:ExplainerView` | Each app registers tabs via `explainer_tabs` on its `AppConfig`. |
| Statistics framework | `views.py:StatisticsView` | Each app registers blocks via `statistics` on its `AppConfig`. |
| Celery + cron entry points | `celery.py`, `tasks.py`, `signals.py`, `metrics.py` | Email delivery, data minimisation cron orchestration, Sentry metric emission helper. |

## What it doesn't have

- Feature-specific tools, models, or business logic. Those live in the feature apps. The `tosti` app should be installable / removable only by the original developers if you wanted to fork TOSTI into something else &mdash; in practice it's always installed.
- A REST API. Public REST endpoints live in `tosti/api/v1/` but that's a routing shell; the actual endpoints are in each feature app's `<app>/api/v1/`.

## Hooks other apps use

Apps register cross-cutting UI by adding methods to their `AppConfig`. The `tosti` app's views walk every `AppConfig`, call the method if present, and stitch the results together. Current hooks:

| Method | Used by | What it does |
| --- | --- | --- |
| `menu_items(request)` | Navbar | Adds nav-menu entries. |
| `user_account_tabs(request)` | `/users/account/` | Adds tabs to the account page. |
| `explainer_tabs(request)` | `/explainers/` | Adds tabs to the explainers page. |
| `statistics(request)` | `/statistics/` | Adds blocks to the statistics page. |
| `announcements(request)` | Banner | Adds inline announcements. |

If you need a new cross-cutting surface, add a new hook here rather than editing other apps' templates.

## Tests

`tests/test_mcp.py` is the cross-cutting test module &mdash; OAuth discovery, dynamic client registration, the `/mcp` auth gate, the consent screen, the connected-apps revoke flow. Per-tool MCP behaviour is tested in each owning app's tests.
</content>
</invoke>