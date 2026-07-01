# How to contribute

This repository is maintained by the website committee of [Tartarus](https://tartarus.science.ru.nl/), reachable at <www-tosti@science.ru.nl>. The project is open source; issues and pull requests are welcome.

If you're an AI coding agent (Claude Code, Cursor, Aider, …), read [`AGENTS.md`](AGENTS.md) instead — it carries the same conventions but is condensed to what an agent needs to make safe edits. Humans should keep reading here.

> [!IMPORTANT]
> Before you build something, read the next section. The scope check is the single load-bearing rule in this project.

---

## Before you build something: does it belong in TOSTI?

TOSTI is the system for the Huygens-building canteens, shared by all study associations that use them. **That's the whole scope.** A new feature only belongs in TOSTI if it meets all three of:

1. **It is canteen-related** — ordering, payments, music, fridges, venue reservations, age checks for the bar, etc.
2. **It is available to all students.** Every authenticated Radboud student can use it.
3. **It is shared with all participating associations.** It serves all of them, not one.

If a proposed feature fails any of these tests, it does not belong in TOSTI. The fact that TOSTI already has authenticated users, OAuth scopes, a venue model, or whatever else makes it tempting to bolt on adjacent things — please don't. Each added feature is a permanent maintenance burden on future volunteers.

**When in doubt, open an issue first** so the website committee can weigh in before code is written.

---

## Quick start

1. **Set up locally.** Follow the [Local development](README.md#-local-development) section in the README — clone, `uv sync`, `migrate`, `runserver`. SAML is disabled in development; use `/admin-login` to sign in as a Django superuser.
2. **Branch off `master`.** Pick a short, descriptive branch name (e.g. `fix-spotify-auto-start`, `add-tampon-form`).
3. **Make your change.** Keep the diff focused — one feature or fix per PR.
4. **Run the checks locally** before opening the PR:
   ```bash
   cd website
   uv run python manage.py test                      # tests
   uv run black website                              # format
   uv run flake8 --exclude="migrations,website/tosti/settings/*.py" \
     --max-line-length=119 website                   # lint
   uv run python manage.py spectacular --validate --api-version v1 > /dev/null
   ```
5. **Open the PR** against `master`. CI must pass (test + lint + image build). Merging to `master` triggers an automatic deploy to <https://tosti.science.ru.nl> via the self-hosted runner. See [`deploy/README.md`](deploy/README.md).

## Project conventions

### Modular Django apps

**Each piece of TOSTI functionality lives in its own Django app, with as few cross-app dependencies as the feature allows.** The intent is that an app can be installed or removed by editing one line in `INSTALLED_APPS`, and the rest of the project keeps working (perhaps with that feature disabled, but with no import errors or broken templates).

Concrete consequences:

- **Models, views, URLs, services, signals, fixtures, templates, and tests** for a feature live inside that feature's app.
- **API endpoints** specific to a feature live in `<app>/api/v1/`.
- **MCP tools** specific to a feature live in `<app>/mcp.py` (auto-discovered by `mcp_server`). For example, music-player tools are in `thaliedje/mcp.py`, ordering tools in `orders/mcp.py`. The `tosti` app exposes only shared helpers (e.g. `tosti.mcp.require_scope`); it does not own any feature-specific tools.
- **Cross-app imports** are allowed for things that are essential to the feature's contract (e.g. `orders` referencing `venues.models.Venue` because shifts happen at venues), but should be kept minimal. If app A merely *enriches* app B, prefer signals or app config hooks over hard imports.
- **App config hooks** (`menu_items`, `user_account_tabs`, `explainer_tabs`, `statistics`) let an app add UI without the `tosti` app having to know about it. Use these instead of editing `tosti/templates/` when you can.

When in doubt: if removing your app from `INSTALLED_APPS` would break an unrelated app, the dependency probably belongs somewhere else.

### Where business logic lives

Models hold data and the invariants that the data layer must enforce (validation, derived properties). Anything else — workflows, side effects, calls into external systems — goes into the app's `<app>/services.py`. Most existing apps follow this pattern (see `orders/services.py`, `thaliedje/services.py`, `tosti/services.py`); please match it. View functions should be thin: parse input, call a service, return a response.

### Migrations

If you change a model, generate the migration in the same commit that introduces the change, and check the migration file in:

```bash
uv run python website/manage.py makemigrations
```

Never edit a migration file that's already on `master`. If you need to fix a bad migration after merging, write a new one. Don't squash other contributors' migrations or rebase to "clean up" the history; deployments rely on the migrations applied in the order they landed.

Avoid destructive migrations (column drops, table drops) without coordinating with the committee — these can lose production data and need to be planned with downtime in mind.

### Fixtures

`<app>/fixtures/*.json` is for **demo / test data only**: things tests load via `fixtures = ["..."]`, or content a fresh dev environment needs to be useful. Production data is not bootstrapped from fixtures — that's what migrations and the admin are for. Don't dump production tables into fixtures, ever.

### Performance and database queries

Several pages in TOSTI poll the API every few seconds (the player widget, the order list, the scanner). A new endpoint that does an N+1 query under polling load becomes a production problem fast.

- Use `select_related` / `prefetch_related` on querysets that traverse foreign keys.
- The project uses [`django-queryable-properties`](https://github.com/W1ldPo1nter/django-queryable-properties); declared queryable properties can be used in `.filter()` and `.annotate()` instead of running per-row Python after a queryset evaluates.
- Don't loop over a queryset in a template/view to compute derived values that need a database hit each time. Push the work into the queryset.
- When in doubt, run with `django.db.connection.queries` enabled and count queries on a representative request.

### Time zones and dates

Django is configured with `USE_TZ=True`. Always use `django.utils.timezone.now()` (never `datetime.now()`) and treat all stored datetimes as UTC-aware. Naive datetimes in fixtures, forms, or tests will trigger `RuntimeWarning: DateTimeField received a naive datetime`. Parse external timestamps with `django.utils.dateparse.parse_datetime` and reject naive results.

### Frontend assets and CSP

The site runs under a strict Content Security Policy (`tosti/settings/base.py`). When you add frontend code:

- Inline `<script>` blocks and `onclick=` handlers require `'unsafe-inline'` in `script-src`. They currently work because that's allowed; tightening it is on the roadmap. Don't add new inline scripts; put the JS in `<app>/static/<app>/js/` and load it with `<script src="{% static '...' %}">`.
- Vue's runtime template compiler uses `new Function(...)`, which needs `'unsafe-eval'`. Don't introduce other libraries that need eval — if you find yourself wanting `eval`/`Function()`, you have a different problem to solve.
- Loading anything from a CDN (fonts, scripts, stylesheets) will be blocked. All third-party assets are vendored under `<app>/static/<app>/`. See the README's "Vendored frontend libraries" section.

### Sensitive apps: `yivi` and `age`

The `yivi/` and `age/` apps implement legally-loaded age verification for the beer fridge. A bug here can result in underage students opening the fridge. Treat these apps as critical: changes need close review, no shortcuts, and any modification of the verification path should come with a corresponding test demonstrating the legal-compliance behaviour still holds. Don't refactor opportunistically; if a change isn't strictly necessary, don't make it.

If you spot a security-sensitive bug in these (or anywhere else), see [`SECURITY.md`](SECURITY.md) — don't open a public issue for it.

### Privacy and PII

TOSTI handles personal data: names, emails, age verifications, transactions, song requests. New features that touch user data must:

- Be covered by the privacy policy at `tosti/templates/tosti/privacy.html`. If your feature stores something the policy doesn't already describe, update the policy in the same PR.
- Honor data minimisation. Long-lived per-user logs need a cron entry in `<app>/crons.py` that prunes or anonymises old records (see `tosti.dataminimisation` for the central cron and `<app>/services.py:execute_data_minimisation` for the per-app hook).
- Never log PII to Sentry or `print()`. Sentry is configured with `send_default_pii=True` for stack traces, but ad-hoc logging of names/emails/ages is not OK.

### Testing

- Each app keeps its own tests under `<app>/tests/test_*.py`. We use a `tests/` package per app — single-file `tests.py` is being phased out.
- Cross-cutting tests live in `tosti/tests/`. For example, the MCP transport / auth-gate / discovery tests are there, while individual MCP tool behaviour is tested in the owning app's test module.
- Use existing fixtures (e.g. `venues.json`) when your test needs venues; don't reinvent setup logic in every test class.
- Don't delete or `@skip` failing tests to make CI pass — fix the underlying bug (or, if the test was wrong, restate the expected behaviour explicitly).
- Run the full suite locally before you push: `uv run python website/manage.py test website/`.

### Code style

- `black` for formatting, `flake8` for linting (line length 119), `pydocstyle` for docstring style. CI runs them all.
- The site is in **English**. Don't introduce Dutch strings into UI text — the canteens are used by international students. The handful of existing Dutch fragments are scoped to legacy or external integrations; don't grow that footprint.
- Heading hierarchy: pages should have one `<h1>` and use `<h2>`/`<h3>` for sections. Use `<p class="lead tagline">` for branding subtitles, not `<h6>`.
- For dropping shared reading-width on text-heavy pages, use the project's `.prose` utility class.

### Frontend dependencies

Vendored under `website/<app>/static/<app>/` or `website/tosti/static/tosti/`. See the README's "Vendored frontend libraries" section for the upgrade procedure. Don't pull in new CDN dependencies — keep CSP tight.

## Opening a pull request

A good PR is short, focused, and self-explanatory:

- **One feature or fix per PR.** Bundling unrelated changes makes review slow and rollbacks risky.
- **PR description.** Say what changed and *why*. Link the issue if there is one. If the change touches an external system (Sentry, Yivi, Spotify, Silvasoft, SURFconext), call that out — it's the kind of thing reviewers can miss.
- **Tests.** If you fix a bug, add a regression test that fails on master and passes on your branch. If you add a feature, cover the happy path plus at least one edge case.
- **Migrations.** If you touched a model, run `makemigrations` and commit the file in the same PR. Flag destructive migrations in the description.
- **Don't squash other people's commits.** Rebases are fine for your own branch; rewriting shared history is not.
- **Don't `--force-push` master or `--no-verify` past hooks.** Ever.

CI runs tests + flake8 + black + image build. All must pass before merge.

## Reviewer checklist

If you're reviewing a PR (whether you're a fellow committee member or a maintainer):

- [ ] Does the change satisfy the scope check at the top of this document?
- [ ] Is it isolated to one app where possible? Cross-app imports justified?
- [ ] If a model changed, is there a migration?
- [ ] If a sensitive app (`age`, `yivi`, `fridges`, `silvasoft`) changed, is there a test that proves the contract still holds?
- [ ] Is there new PII being logged or stored? If stored, is the privacy policy updated?
- [ ] Are new frontend assets vendored, not CDN-loaded?
- [ ] CI green?

Once merged, the change ships to <https://tosti.science.ru.nl> automatically. Treat every merge as a deploy.

## Getting help

If you're stuck:

- Open a draft PR and tag the website committee — early feedback beats a long-running branch.
- Email <www-tosti@science.ru.nl>.
- For security-sensitive questions, see [`SECURITY.md`](SECURITY.md).
</content>
</invoke>