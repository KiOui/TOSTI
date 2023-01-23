import os
from pathlib import Path

import saml2
from django.contrib import messages
from saml2 import saml, xmldsig

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
    "tosti.django_cron_app_config.CustomDjangoCronAppConfig",
    "djangosaml2",
    "django_bootstrap5",
    "tinymce",
    "fontawesomefree",
    "autocompletefilter",
    "import_export",
    "guardian",
    'rest_framework',
    'django_filters',
    'rangefilter',
    "announcements",
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
    "djangosaml2.backends.Saml2Backend",
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
    "djangosaml2.middleware.SamlSessionMiddleware",
    "announcements.middleware.ClosedAnnouncementsMiddleware",
]

ROOT_URLCONF = "tosti.urls"

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
SAML_SESSION_COOKIE_NAME = "saml_session"
SESSION_COOKIE_SECURE = False
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/users/account/'
# LOGIN_URL = "/saml/login/"
# LOGOUT_REDIRECT_URL = "/saml/login/"
# LOGIN_REDIRECT_URL = "/"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
BASE_URL = "tosti.science.ru.nl"
SAML_USE_NAME_ID_AS_USERNAME = True
SAML_ATTRIBUTE_MAPPING = {
    "uid": ("username",),
    "mail": ("email",),
    "displayName": ("full_name",),
}
SAML_CONFIG = {
    "xmlsec_binary": "/usr/bin/xmlsec1",
    "entityid": BASE_URL,
    "allow_unknown_attributes": True,
    "service": {
        "sp": {
            "name": "TOSTI",
            "name_id_format": saml.NAMEID_FORMAT_PERSISTENT,
            "endpoints": {
                "assertion_consumer_service": [
                    (f"https://{BASE_URL}/sso/science/acs/", saml2.BINDING_HTTP_POST), # Legacy
                    (f"https://{BASE_URL}/saml/acs/", saml2.BINDING_HTTP_POST),
                ],
                "single_logout_service": [
                    (f"https://{BASE_URL}/sso/science/ls/", saml2.BINDING_HTTP_REDIRECT), # Legacy
                    (f"https://{BASE_URL}/sso/science/ls/post", saml2.BINDING_HTTP_POST), # Legacy
                    (f"https://{BASE_URL}/saml/ls/", saml2.BINDING_HTTP_REDIRECT),
                    (f"https://{BASE_URL}/saml/ls/post", saml2.BINDING_HTTP_POST),
                ],
            },
            "signing_algorithm": xmldsig.SIG_RSA_SHA256,
            "digest_algorithm": xmldsig.DIGEST_SHA256,
            "force_authn": False,
            "name_id_format_allow_create": True,
            "required_attributes": ["uid", "mail", "displayName"],
            "want_response_signed": False,
            "want_assertions_signed": True,
            "allow_unsolicited": True,
        },
    },
    "metadata": {
        "local": [
            os.path.join(BASE_DIR, "tosti", "settings", "metadata.xml"),
        ],
    },
    "debug": 1,
    "key_file": os.path.join(BASE_DIR, "tosti", "settings", "private.key"),
    "cert_file": os.path.join(BASE_DIR, "tosti", "settings", "public.cert"),
    "encryption_keypairs": [
        {
            "key_file": os.path.join(BASE_DIR, "tosti", "settings", "private.key"),
            "cert_file": os.path.join(BASE_DIR, "tosti", "settings", "public.cert"),
        }
    ],
    "contact_person": [
        {
            "given_name": "Olympus",
            "email_address": "www-tosti@science.ru.nl",
            "contact_type": "technical",
        },
        {
            "given_name": "Olympus",
            "email_address": "www-tosti@science.ru.nl",
            "contact_type": "administrative",
        },
    ],
    "organization": {
        "name": [("Olympus", "nl"), ("Olympus", "en")],
        "display_name": [
            ("Olympus", "nl"),
            ("Olympus", "en"),
        ],
        "url": [
            (BASE_URL, "nl"),
            (BASE_URL, "en"),
        ],
    },
}

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
        'noreply@example.com, noreply@example.com', 'Where to send venue reservation request notifications to (e-mail address), enter multiple addresses by using a comma (,)', str),
    'SHIFTS_DEFAULT_MAX_ORDERS_TOTAL': (70, 'Default maximum number of orders per shift', int),
    'THALIEDJE_STOP_PLAYERS_AT': ("21:00", 'Time to stop the players. Should be aligned on 5 minutes', str),
    'THALIEDJE_START_PLAYERS_AT': ("08:00", 'Time to start the players (only on weekdays). Should be aligned on 5 minutes', str),
    'THALIEDJE_HOLIDAY_ACTIVE': (False, 'If enabled, the player will not start playing automatically at the start of the day', bool),
}

CONSTANCE_CONFIG_FIELDSETS = {
    'General settings': ('FOOTER_CREDITS_TEXT', 'CLEANING_SCHEME_URL',),
    'Tantalus settings': ('TANTALUS_ENDPOINT_URL', 'TANTALUS_API_URL', 'TANTALUS_USERNAME', 'TANTALUS_PASSWORD',),
    'E-mail settings': ('BORREL_SEND_BORREL_RESERVATION_REQUEST_EMAILS_TO', 'VENUES_SEND_RESERVATION_REQUEST_EMAILS_TO'),
    'Shifts settings': ('SHIFTS_DEFAULT_MAX_ORDERS_TOTAL',),
    'Thaliedje settings': ('THALIEDJE_STOP_PLAYERS_AT', 'THALIEDJE_START_PLAYERS_AT', 'THALIEDJE_HOLIDAY_ACTIVE'),
}

# Sites app
SITE_ID = 1

CRON_CLASSES = [
    "thaliedje.crons.StopMusicCronJob",
    "thaliedje.crons.StartMusicCronJob",
]

DJANGO_CRON_DELETE_LOGS_OLDER_THAN = 14
