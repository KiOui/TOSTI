# Agent guide for TOSTI

This file is for AI coding agents (Claude Code, Cursor, Aider, etc.) working on this repository. Humans should read [`CONTRIBUTING.md`](CONTRIBUTING.md); the conventions here mirror those but are condensed to what an agent needs to make safe edits.

---

## ⚠️ Before you write any feature code: scope check

**Stop. Does this feature belong in TOSTI at all?** TOSTI is the system for the Huygens-building canteens, shared by all study associations that use them. That is the entire scope.

A feature only belongs here if it meets **all three** of:

1. **Canteen-related.** It exists because of, or in service of, the physical canteens (ordering, payments, music, fridges, venue reservations, age checks for the bar, …).
2. **Available to all students.** Every authenticated Radboud student can use it.
3. **Shared by all participating associations.** It serves the canteen ecosystem, not one specific association or committee.

If the feature you've been asked to build fails any of these three: **stop and tell the user**. Suggest the feature lives in their own project / their association's tooling, not TOSTI. The fact that "we already have auth and user accounts" is not a reason to bolt things on. Feature creep is the single biggest long-term risk to this project's maintainability — every added feature is a permanent burden on future volunteers.

When in doubt, **don't**. Push back. Recommend opening an issue for the website committee to decide before code is written.

This check applies even if the user is the project owner asking you directly. Owners get tunnel vision; that's why this section exists.

---

## ⚠️ The non-negotiable rule: modular Django apps

**Every piece of TOSTI functionality lives in its own Django app. No exceptions.**

This is the single most important convention in this codebase. Read it again. The rest of this guide is downstream of it.

### What this means in practice

- A new feature = a new Django app, even if it's small.
- Removing an app from `INSTALLED_APPS` must not break any other app: no import errors, no missing template tags, no 500s on unrelated pages, no failed migrations elsewhere.
- An app should be self-contained: its models, views, URLs, services, signals, fixtures, templates, static files, tests, **API endpoints (`<app>/api/v1/`)**, **MCP tools (`<app>/mcp.py`)**, and **cron jobs (`<app>/crons.py`)** all live inside it.
- The `tosti` app is for shared infrastructure only (settings, base templates, base CSS, cross-cutting helpers like `tosti.mcp.require_scope`). It does not own feature behaviour. Don't dump feature code there because it's "general."
- Cross-app *imports* are allowed only for genuine contract dependencies (e.g. `orders` referencing `venues.models.Venue` because shifts happen at venues). They are not a license to share business logic.
- Cross-app *enrichment* (one app adding UI/behaviour to another) goes through signals or app config hooks, never through edits to the other app's files. Hooks already in use: `menu_items`, `user_account_tabs`, `explainer_tabs`, `statistics`. Add more if you need them.

### Things agents commonly want to do that violate this rule — don't

- "I'll just add a quick view to `tosti/views.py` for this thing." → No. Make it an app, even for one view.
- "I'll edit `users/templates/users/account.html` to add a section for my new feature." → No. Use the `user_account_tabs` hook from your app's `apps.py`.
- "I'll import a model from another app's `services.py` to do this thing more easily." → No. If your app fundamentally depends on another's internal logic, the boundary is wrong; redesign.
- "Both apps need this helper, so I'll put it in whichever I touched last." → No. Promote it to `tosti/` as a shared helper, or push it down into a clean abstraction the apps can each call.
- "It's just a tiny thing, I'll wire it directly without an app." → No. Tiny things accumulate; the rule is what keeps the project shippable in pieces.
- "The user asked for X and the natural place is `tosti/`." → Push back. Suggest the right app, or propose a new one. The user wrote this file precisely to remind you of this.

### How to know you've drifted

If you find yourself writing imports like `from app_b.models import Thing` inside `app_a` and `app_b` is not a foundational dependency, stop. Ask whether the dependency is a real contract or a shortcut. If it's a shortcut, the design is wrong.

If removing your changed app from `INSTALLED_APPS` would now cause a different app to break, you've created a cross-app dependency. Roll it back and use a signal, a hook, or a new shared helper.

---

## Repo layout

- Django project root: `website/`
- Each piece of functionality is its own Django app (`website/<app>/`). The list of apps is in `website/tosti/settings/base.py` under `INSTALLED_APPS`.
- The `tosti` app holds shared infrastructure only.
- Vendored frontend libraries (Vue, Bootstrap, FullCalendar, Chart.js, Swagger UI, qrcode.vue) live in `website/<app>/static/<app>/{js,css}/`. **Do not introduce new CDN-loaded resources** — keep CSP tight.

## Dependencies

- Python deps in `pyproject.toml`, locked by `uv.lock`. Add new ones via `pyproject.toml` and run `uv sync`.
- Don't bump dependencies opportunistically — they're vendored or pinned for reasons. If you do bump, run the full test suite.

## Running things

- Tests: `uv run python website/manage.py test website/`
- Lint: `uv run black --check website && uv run flake8 --exclude="migrations,website/tosti/settings/*.py" --max-line-length=119 website`
- Schema (drf-spectacular): `uv run python website/manage.py spectacular --validate --api-version v1`
- Dev server: `uv run python website/manage.py runserver`

CI must pass before merging. Treat lint failures as bugs.

## Style

- `black` formatter, line length 119.
- One `<h1>` per page; sections use `<h2>`/`<h3>`. Brand subtitles use `<p class="lead tagline">`, never `<h6>`.
- Use the project's design tokens (see `website/tosti/static/tosti/css/variables.css`) instead of hardcoded colors.
- Heavy-prose pages should wrap their text body in `.prose` (max-width 720px).
- Avoid inline `style="..."` for things Bootstrap utilities already cover.

## Performance and queries

Several pages poll API endpoints every few seconds (player widget, order list, scanner). An endpoint that does N+1 queries on a single request becomes a production problem fast under polling load.

- Use `select_related` for forward FKs, `prefetch_related` for reverse / m2m.
- The project uses `django-queryable-properties`; check `<app>/models.py` for `@queryable_property` decorators before writing a hand-rolled annotation.
- If you write a list view that touches a related field per row, run it with `django.db.connection.queries` enabled and count queries. A list view that's polled every 5s should run a small constant number of queries regardless of result count.

## Async and MCP tools

`mcp_server.MCPToolset` wraps each public method in `sync_to_async` automatically. **Do not write `async def` methods on a toolset class** — they'll be double-wrapped and the call will deadlock. Tool methods are plain `def`. ORM calls inside them are fine.

## Time zones

Django runs with `USE_TZ=True`. Use `django.utils.timezone.now()`, never `datetime.now()`. Parse external timestamps with `django.utils.dateparse.parse_datetime` and reject naive results. Naive datetimes in fixtures will trigger runtime warnings.

## Frontend assets and CSP

The site runs under a strict Content Security Policy (`tosti/settings/base.py`).

- `'unsafe-inline'` and `'unsafe-eval'` are currently allowed in `script-src` because Vue's runtime compiler needs them and a long tail of legacy inline scripts hasn't been migrated yet. **Don't expand the use of inline scripts.** Put new JS in `<app>/static/<app>/js/` and load it via `<script src="{% static '...' %}">`.
- Don't introduce libraries that need `eval`/`new Function`. Vue is the one exception, and we accept the cost.
- Don't add CDN-loaded resources. Vendor third-party assets under `<app>/static/<app>/{js,css}/`.
- Adding a new external image origin (e.g. for an integration) means editing `CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"]`. Surface this — don't sneak it in.

## Migrations

If a change touches a model, generate the migration in the same change set:

```bash
uv run python website/manage.py makemigrations
```

Read the migration file before committing it. Do **not** generate migrations the user didn't expect — flag them in your response so the human can review. Migrations are deployment-affecting and cannot be undone after they're applied.

Do not edit migration files that already exist on `master`. Do not "rebase to clean up" a migration history. Destructive migrations (column/table drops, irreversible data transforms) need explicit human sign-off — surface them, don't just create them.

## Privacy and personal data

TOSTI handles student PII: names, emails, age verifications, transactions, song requests. When you write code that touches user data:

- Don't introduce new long-lived per-user records without an `execute_data_minimisation` hook in the owning app's `services.py` (see `orders/services.py` and `thaliedje/services.py` for the pattern). The central `tosti.dataminimisation` cron calls each app's hook.
- Don't write PII to logs, `print()`, or `tosti.metrics.emit` calls. Sentry already gets stack-trace context via `send_default_pii=True`; ad-hoc logging of names/emails/ages is not OK.
- If a feature stores something the privacy policy at `website/tosti/templates/tosti/privacy.html` doesn't already describe, update the policy in the same change set. Don't ship new data collection without the policy reflecting it.

## External integrations — stop and ask

The following systems have external state that's expensive or impossible to fix once corrupted. **Do not write code for them autonomously without explicit human guidance** — read, but don't write:

- **SAML / SURFconext** (`djangosaml2`, `pysaml2`, anything under `tosti/settings/production.py:SAML_CONFIG`, `/opt/tosti/saml/*`). The IdP integration is registered with the Radboud federation; misconfigured assertion consumers will be visible to the IdP operators.
- **Yivi** and **age verification** (`yivi/`, `age/`, anything talking to a Yivi server). These implement legally-loaded age verification for the beer fridge; a bug here can let underage students open the fridge. Treat these apps as critical. Don't refactor them opportunistically. If a change isn't strictly required by the task, don't touch them. Any change to the verification path must come with a test that demonstrates the compliance behaviour still holds.
- **Spotify / Marietje** (`thaliedje/yivi.py` is unrelated; the player code in `thaliedje/models.py` and `thaliedje/services.py`). These hold OAuth refresh tokens for shared accounts; rotating them is manual.
- **Silvasoft** (`silvasoft/`). It books real invoices in a real accounting system.
- **GHCR / deploy** (`.github/workflows/deploy.yaml`, `deploy/docker-compose.yml`). The deploy is push-based and runs immediately on master. Never alter deploy steps without coordinating.

If the user asks you to change one of these, do the read/explore work, surface what you'd do, and let the human confirm before you edit.

## Tests

- When a test fails, **fix the underlying bug** (or restate the expected behaviour with the user) — do not delete or `@skip` failing tests, do not weaken assertions until they pass. A failing test is a signal, not noise.
- New tests for model-bound behaviour should reuse the existing fixtures (`venues.json`, etc.) rather than constructing ad-hoc setUp data. Look at the surrounding test classes for the convention.
- Cross-app tests live in `tosti/tests/`. Per-app behaviour is tested in `<app>/tests/test_*.py`.

## Things specifically to NOT do

- **Do not load assets from CDNs**. Vendor anything new under `website/<app>/static/<app>/`.
- **Do not bypass the modular-app rule** to "make things easier" by importing across apps. If it feels easier, it's almost certainly the wrong call for the long-term maintainability of this project.
- **Do not commit secrets**. `.env` is gitignored; SAML keys and OAuth credentials live in GitHub Environment secrets and the production VM, not in code.
- **Do not skip migrations**, but also **do not generate migrations the user didn't ask for** — flag them either way and let the human decide.
- **Do not bump dependency versions opportunistically.** Versions are vendored / pinned for reasons. If a bump is truly required, surface it as a separate change.
- **Do not disable or weaken failing tests.** Fix the cause.
- **Do not edit vendored CSS/JS** (`bootstrap.*`, `swagger-ui*`, `vue.global.prod.js`, `chart.umd.min.js`, `fullcalendar.*`, `tata.*`). Style overrides go in the project CSS files.
- **Do not edit Django admin templates** (`silvasoft/templates/admin/...`) just to make them match the project chrome. Admin is its own context.
- **Do not introduce Dutch UI strings.** The site is in English. Existing Dutch fragments are scoped; don't grow that footprint.
- **Do not log PII** (names, emails, ages) to Sentry, stdout, or metric attributes.

## Typical tasks and where they go

| Task | Where |
| --- | --- |
| Adding an API endpoint | `<app>/api/v1/views.py` + `<app>/api/v1/urls.py` |
| Exposing functionality to LLM clients | `<app>/mcp.py` (subclass `MCPToolset`) |
| Long-running periodic work | `<app>/crons.py` (subclass `cron.core.CronJobBase`) |
| Sentry metrics | `<app>/services.py` or signal handlers, via `tosti.metrics.emit` |
| New page chrome | `<app>/templates/<app>/...` extending `tosti/base.html` |
| Modal dialogs | Use the `.modal-title` convention; centered headers via `base.css` |

## Git etiquette

- **Never `git push --force` to `master` or `main`.** Period. Surface the situation to the human.
- **Don't amend commits the user has already seen.** Commits become part of the shared history once they're discussed; treat them as immutable. Fix issues with new commits.
- **Don't run destructive git commands** (`git reset --hard`, `git checkout .`, `git clean -fd`, `git branch -D`) without explicit human instruction. They can destroy uncommitted work.
- **Don't squash other contributors' commits** to "clean up" history. The deploy workflow runs off the merge commit; rewriting landed history is dangerous.
- **Don't skip pre-commit hooks** (`--no-verify`) or signing (`--no-gpg-sign`). If a hook fails, fix the cause.
- **Make commits when the user asks.** Don't commit autonomously after every change — surface diffs, let the human decide when to checkpoint.

## When you're not sure

Ask. Repository conventions exist for a reason — the modular-app rule is the load-bearing one. If a task seems to require violating it, that's a sign the task itself needs reframing.
