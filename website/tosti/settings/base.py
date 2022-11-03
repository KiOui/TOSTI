from pathlib import Path

from django.contrib import messages

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = [
    "tosti",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "constance",
    "constance.backends.database",
    "tosti.sp_app_config.CustomSPAppConfig",
    "django_bootstrap5",
    "fontawesomefree",
    "autocompletefilter",
    "import_export",
    "guardian",
    'rest_framework',
    'django_filters',
    "users",
    "venues",
    "associations",
    "borrel",
    "thaliedje",
    "orders",
    "tantalus",
    "oauth2_provider",
    "corsheaders",
]

AUTH_USER_MODEL = 'users.User'

ANONYMOUS_USER_NAME = None

GUARDIAN_RAISE_403 = True

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
    "sp.backends.SAMLAuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
]

ROOT_URLCONF = "tosti.urls"

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/users/account/'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tosti.context_processors.google_analytics",
                "tosti.context_processors.footer_credits",
            ],
        },
    },
]

WSGI_APPLICATION = "tosti.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Amsterdam"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# REST FRAMEWORK
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    'DEFAULT_SCHEMA_CLASS': 'tosti.api.openapi.CustomAutoSchema',
}

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(?:api|user/oauth)/.*"

DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000

# OAUTH
OAUTH2_PROVIDER = {
    "ALLOWED_REDIRECT_URI_SCHEMES": ["https", "nu.thalia"],
    "SCOPES": {
        "read": "Authenticated read access to the website",
        "write": "Authenticated write access to the website",
        "orders:order": "Place orders on your behalf",
        "orders:manage": "Manage orders on your behalf",
        "thaliedje:request": "Request songs on your behalf",
        "thaliedje:manage": "Manage music players on your behalf",
    },
}

# SAML SP SETTINGS
SP_UNIQUE_USERNAMES = False
SP_LOGIN = "users.services.post_login"
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

# Messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info info',
    messages.INFO: 'alert-info info',
    messages.SUCCESS: 'alert-success success',
    messages.WARNING: 'alert-warning warning',
    messages.ERROR: 'alert-danger danger',
}

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_CONFIG = {
    'FOOTER_CREDITS_TEXT': ('TOSTI - Tartarus Order System for Take-away Items',
                            'Text to display in the footer credits', str),
    'CLEANING_SCHEME_URL': ('', 'URL to the cleaning scheme to be accepted when submitting a borrel form', str),
    'TANTALUS_ENDPOINT_URL': ('', 'Endpoint for Tantalus integration', str),
    'TANTALUS_API_URL': ('', 'Endpoint for Tantalus API', str),
    'TANTALUS_USERNAME': ('', 'Username for Tantalus integration', str),
    'TANTALUS_PASSWORD': ('', 'Password for Tantalus integration', str),
    'BORREL_SEND_BORREL_RESERVATION_REQUEST_EMAILS_TO': (
        'noreply@example.com', 'Where to send borrel reservation request notifications to (e-mail address)', str),
    'VENUES_SEND_RESERVATION_REQUEST_EMAILS_TO': (
        'noreply@example.com', 'Where to send venue reservation request notifications to (e-mail address)', str),
    'SHIFTS_DEFAULT_MAX_ORDERS_TOTAL': (70, 'Default maximum number of orders per shift', int),
}

CONSTANCE_CONFIG_FIELDSETS = {
    'General settings': ('FOOTER_CREDITS_TEXT', 'CLEANING_SCHEME_URL',),
    'Tantalus settings': ('TANTALUS_ENDPOINT_URL', 'TANTALUS_API_URL', 'TANTALUS_USERNAME', 'TANTALUS_PASSWORD',),
    'E-mail settings': ('BORREL_SEND_BORREL_RESERVATION_REQUEST_EMAILS_TO', 'VENUES_SEND_RESERVATION_REQUEST_EMAILS_TO'),
    'Shifts settings': ('SHIFTS_DEFAULT_MAX_ORDERS_TOTAL',),
}

# Sites app
SITE_ID = 1
