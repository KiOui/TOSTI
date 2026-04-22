# TOSTI - Tartarus Order System for Take-away Items

[![CI](https://github.com/KiOui/TOSTI/actions/workflows/ci.yaml/badge.svg)](https://github.com/KiOui/TOSTI/actions/workflows/ci.yaml)
[![Deploy](https://github.com/KiOui/TOSTI/actions/workflows/deploy.yaml/badge.svg)](https://github.com/KiOui/TOSTI/actions/workflows/deploy.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

TOSTI is a comprehensive web application designed for [Tartarus](https://tartarus.science.ru.nl) to manage take-away orders and various other features for student associations at Radboud University.

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
- **Backend**: Django 5.1 (Python)
- **Frontend**: Django templates with Bootstrap 5
- **Database**: PostgreSQL (production) / SQLite (development)
- **Caching**: File-based cache (production) / In-memory (development)
- **Authentication**: SAML2 (via djangosaml2)
- **API**: Django REST Framework with OAuth2
- **Task Scheduling**: Custom cron implementation
- **Containerization**: Docker & Docker Compose

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
