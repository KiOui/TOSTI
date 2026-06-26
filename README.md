# TOSTI - Tartarus Order System for Take-away Items

[![CI](https://github.com/KiOui/TOSTI/actions/workflows/ci.yaml/badge.svg)](https://github.com/KiOui/TOSTI/actions/workflows/ci.yaml)
[![Deploy](https://github.com/KiOui/TOSTI/actions/workflows/deploy.yaml/badge.svg)](https://github.com/KiOui/TOSTI/actions/workflows/deploy.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

TOSTI is a comprehensive web application designed for [Tartarus](https://tartarus.science.ru.nl) to manage take-away orders and various other features for student associations at Radboud University.

## 🎯 Scope — what belongs in TOSTI

**TOSTI is the system for the Huygens-building canteens, shared by all study associations that use them.** That's the entire scope. Before adding a feature, check that it satisfies all three of these conditions:

1. **Canteen-related.** The feature exists because of, or in service of, the physical canteens (ordering, payments, music, fridges, venue reservations, age checks for the bar, …). If you can build it without TOSTI being a canteen system, it doesn't belong here.
2. **Available to all students.** Every authenticated Radboud student can use it. Features that only serve one association, one committee, or a private subset of users belong in that group's own tooling, not in TOSTI.
3. **Shared by all participating associations.** A feature that benefits one association but not the others is out of scope. Build it in that association's own systems.

If a proposed feature fails any of these tests, it doesn't belong in TOSTI — even if it's well-built, even if it's small, even if "we already have the auth and the user accounts so it'd be easy to bolt on." Resist that. Feature creep is the single biggest risk to this project's long-term maintainability. Each added feature is a permanent maintenance burden carried by future volunteers.

When in doubt, **don't**. Open an issue and let the website committee weigh in before writing code.

## 🚀 Features

### Core Features
- **Order Management System**: Online ordering system for take-away items (such as tostis)
- **Financial Transactions**: User balance tracking and transaction management
- **User Authentication**: SAML-based SSO integration (with Radboud University via SURFconext)
- **Music Control**: Spotify and Marietje integration for controlling music players
- **Room Reservations**: Venue reservation system with calendar integration
- **Borrel Management**: Event reservation system with inventory tracking
- **Age Verification**: Yivi-based age verification system
- **Smart Fridge Access**: Digital lock system for automated fridge access, using [TOSTI-fridge-client](https://github.com/KiOui/TOSTI-fridge-client)
- **QR Code Identification**: Token-based user identification system
- **Bookkeeping Integration**: Synchronization with Silvasoft accounting system

### Additional Features
- Multi-venue support with separate canteens (North/South)
- Real-time order status tracking
- Statistics and analytics dashboard
- OAuth2 API for third-party integrations
- iCal feeds for reservations
- Automated music scheduling

## 🏗️ Architecture

TOSTI is built using:
- **Backend**: Django 6 (Python)
- **Frontend**: Django templates with Bootstrap 5
- **Database**: PostgreSQL (production) / SQLite (development)
- **Caching**: File-based cache (production) / In-memory (development)
- **Authentication**: SAML2 (via djangosaml2)
- **API**: Django REST Framework with OAuth2 + drf-spectacular for OpenAPI
- **MCP server**: in-process (`django-mcp-server`) at `/mcp`
- **Task Scheduling**: Custom cron implementation
- **Containerization**: Docker & Docker Compose

### Modular Django apps

Each piece of TOSTI functionality lives in its own Django app, with **minimal cross-app dependencies**. The goal is that adding or removing a feature should be as simple as adding or removing a line from `INSTALLED_APPS` — no other app should break, no template should fail to render, no URL should 500.

In practice this means: models, views, URLs, services, signals, API endpoints (`<app>/api/v1/`), and **MCP tools** (`<app>/mcp.py`) for a feature all live inside that feature's app. The `tosti` app contains only shared infrastructure (settings, base templates, cross-cutting helpers). When you build a new feature, build it as its own app — see `CONTRIBUTING.md` for the conventions.

## 📁 Project Structure

```
website/
├── age/                    # Age verification module
├── announcements/          # System announcements
├── associations/           # Student associations management
├── borrel/                 # Event/borrel reservation system
├── cron/                   # Custom cron job implementation
├── fridges/                # Smart fridge access control
├── orders/                 # Core ordering system
├── qualifications/         # User qualifications (e.g., borrel brevet)
├── silvasoft/              # Bookkeeping integration
├── status_screen/          # Order status display
├── thaliedje/              # Music player control
├── tosti/                  # Main application settings
├── transactions/           # Financial transactions
├── users/                  # User management
├── venues/                 # Venue reservation system
└── yivi/                   # Yivi integration for age verification
```

## 🛠️ Development Setup

### Prerequisites
- Python 3.14+ (recommended to use [pyenv](https://github.com/pyenv/pyenv))
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/KiOui/TOSTI.git
   cd TOSTI
   ```

2. **Install uv**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up uv environment**
   ```bash
   uv sync --locked --all-extras --dev
   ```

4. **Set up the database**
   ```bash
   cd website
   uv run ./manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   uv run ./manage.py createsuperuser
   ```

6. **Load initial data (optional)**
   ```bash
   uv run ./manage.py loaddata tosti/fixtures/default.json
   ```

7. **Run the development server**
   ```bash
   uv run ./manage.py runserver
   ```

The application will be available at `http://localhost:8000`.

### Development Notes
- SAML authentication is disabled in development mode
- Use `/admin-login` in production for local authentication
- API documentation is available at `/api/docs`

### Vendored frontend libraries

All third-party JS/CSS is vendored in-repo — no CDN dependencies at runtime. To bump versions:

```bash
# Vue (use the production build only — the dev build emits a runtime warning)
curl -sfL https://unpkg.com/vue@<X.Y.Z>/dist/vue.global.prod.js \
  -o website/tosti/static/tosti/js/vue.global.prod.js

# qrcode.vue
curl -sfL https://unpkg.com/qrcode.vue@<X.Y.Z>/dist/qrcode.vue.browser.min.js \
  -o website/tosti/static/tosti/js/qrcode.vue.browser.min.js

# Chart.js (used on the statistics page; the bundle references its sourcemap)
curl -sfL https://cdn.jsdelivr.net/npm/chart.js@<X.Y.Z>/dist/chart.umd.min.js \
  -o website/tosti/static/tosti/js/chart.umd.min.js
curl -sfL https://cdn.jsdelivr.net/npm/chart.js@<X.Y.Z>/dist/chart.umd.min.js.map \
  -o website/tosti/static/tosti/js/chart.umd.min.js.map

# FullCalendar 6+ — CSS is inlined into the JS, no separate stylesheet
curl -sfL https://cdn.jsdelivr.net/npm/fullcalendar@<X.Y.Z>/index.global.min.js \
  -o website/venues/static/venues/js/fullcalendar.index.global.min.js

# Bootstrap (grab both minified and unminified + source maps)
BS=<X.Y.Z>
for f in js/bootstrap.bundle.js js/bootstrap.bundle.js.map \
         js/bootstrap.bundle.min.js js/bootstrap.bundle.min.js.map \
         css/bootstrap.css css/bootstrap.css.map \
         css/bootstrap.min.css css/bootstrap.min.css.map; do
  curl -sfL "https://cdn.jsdelivr.net/npm/bootstrap@$BS/dist/$f" \
    -o "website/tosti/static/tosti/$f"
done

# Swagger UI (used on /api/docs)
SW=<X.Y.Z>
for f in swagger-ui-bundle.js swagger-ui-bundle.js.map \
         swagger-ui-standalone-preset.js swagger-ui-standalone-preset.js.map; do
  curl -sfL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@$SW/$f" \
    -o "website/tosti/static/tosti/js/$f"
done
for f in swagger-ui.css swagger-ui.css.map; do
  curl -sfL "https://cdn.jsdelivr.net/npm/swagger-ui-dist@$SW/$f" \
    -o "website/tosti/static/tosti/css/$f"
done
```

The Neucha font is also self-hosted under `website/tosti/static/tosti/fonts/`.

Verify Vue: `head -2 website/tosti/static/tosti/js/vue.global.prod.js` should print the expected version, and the file should be a single-line minified bundle (not ~16 000 lines of source — that would be the dev build in disguise).

## 🐳 Production Deployment

TOSTI runs in production as a Docker Compose stack on a VM. Deployments are automated: every push to `master` that passes CI (test + lint + image build) is deployed by `.github/workflows/deploy.yaml`.

Deployment configuration — `docker-compose.yml`, `Caddyfile`, `.env.example` — lives in [`deploy/`](deploy/). See [`deploy/README.md`](deploy/README.md) for VM prerequisites, required GitHub secrets, and rollback procedure.

To run the stack manually (e.g. on a fresh VM before CI is wired up):

```bash
cd deploy
cp .env.example .env  # fill in POSTGRES_PASSWORD, DJANGO_SECRET_KEY, YIVI_TOKEN, SENTRY_DSN
docker compose up -d
```

## 🔧 Configuration

Specific configuration is managed through Django Constance for runtime settings:

- **General**: Footer text, cleaning scheme URL
- **Email**: Notification recipients for reservations
- **Shifts**: Default maximum orders per shift
- **Music (Thaliedje)**: Start/stop times, holiday mode
- **Silvasoft**: API credentials for bookkeeping
- **Fridges**: Daily opening requirements

## 📡 API

TOSTI provides a RESTful API with OAuth2 authentication.

### Available Scopes
- `read`: Read access to the API
- `write`: Write access to the API
- `orders:order`: Place orders
- `orders:manage`: Manage all orders
- `thaliedje:request`: Request songs
- `thaliedje:manage`: Control music players
- `transactions:write`: Create transactions

### API Documentation
Interactive API documentation is available at `/api/docs` when running the application.

### MCP server (Model Context Protocol)

TOSTI exposes a small subset of the API as LLM-callable tools at `/mcp`. This lets any MCP-compatible AI assistant read state and act on the user's behalf with the same OAuth2 / session credentials they'd use for the REST API.

Each app contributes its own tools via an `<app>/mcp.py` module, auto-discovered by `django-mcp-server`. To add a tool, drop a method on a `MCPToolset` subclass in the relevant app — no central registration. Tools currently published:

| Tool | Owning app | Required scope | Description |
| --- | --- | --- | --- |
| `list_venues` | `venues` | none | List all venues. |
| `create_venue_reservation` | `venues` | `write` | Request (unaccepted) a venue reservation. |
| `list_active_shifts` | `orders` | none | List shifts currently open for ordering. |
| `place_order` | `orders` | `orders:order` | Place a single-item order in an active shift. |
| `get_player_state` | `thaliedje` | none | Current track & playback state for a venue's player. |
| `search_tracks` | `thaliedje` | none | Search the music catalog via a venue's player. |
| `request_song` | `thaliedje` | `thaliedje:request` | Add a track to a player's queue. |

**Auth flow** (works with any RFC-compliant MCP client):

1. Client POSTs to `/mcp` without credentials → server returns `401` with `WWW-Authenticate: Bearer realm="tosti", resource_metadata="https://tosti.science.ru.nl/.well-known/oauth-protected-resource"`.
2. Client GETs the resource metadata (RFC 9728) → discovers the authorization server.
3. Client GETs `/.well-known/oauth-authorization-server` (RFC 8414) → discovers the `registration_endpoint`, `authorization_endpoint`, `token_endpoint`, supported scopes, etc.
4. Client POSTs to `/oauth/register/` (RFC 7591) with its redirect URIs → server creates a public OAuth2 application on the fly and returns the `client_id`.
5. Client runs the standard authorization-code-with-PKCE flow. User logs in via SAML → SURFconext → user lands on TOSTI's consent screen → approves the scopes the client asked for.
6. Client receives an access token; subsequent MCP calls go to `/mcp` with `Authorization: Bearer <token>`.

Authenticated MCP requests pass through `OAuth2Authentication` (or `SessionAuthentication` for the browser-flow case) — same chain as DRF.

## 🧪 Testing

Run the test suite:
```bash
cd website
uv run python manage.py test
```

Run with coverage:
```bash
uv run coverage run website/manage.py test website/
uv run coverage report
```

## 🔍 Code Quality

### Linting
```bash
uv run black website
uv run flake8 website
uv run pydocstyle website
```

### Checks
The project uses GitHub Actions for automated testing and linting on every push.

## 🤝 Contributing

Contributions are welcome! 

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Code Style
- Follow PEP 8
- Use Black for formatting
- Write docstrings for all functions
- Maximum line length: 119 characters

## 📧 Contact

- **Maintainers**: Website committee of Tartarus
- **Email**: tartaruswebsite@science.ru.nl
- **Security Issues**: www-tosti@science.ru.nl

## 🔒 Security

For security vulnerabilities, please email www-tosti@science.ru.nl instead of creating a public issue.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original developers: Lars van Rhijn, Job Doesburg
- All contributors who have helped improve TOSTI
- - CNCZ for hosting infrastructure
