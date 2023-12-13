import os

from .base import *

import saml2
from saml2 import saml, xmldsig

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import ignore_logger

ignore_logger("django.security.DisallowedHost")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = [os.environ.get("DJANGO_ALLOWED_HOST")]

SESSION_COOKIE_SECURE = True


# Databases
# https://docs.djangoproject.com/en/3.2/ref/databases/

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": int(os.environ.get("POSTGRES_PORT", 5432)),
        "NAME": os.environ.get("POSTGRES_NAME"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
    }
}


# Logging
# https://docs.djangoproject.com/en/3.2/topics/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "/tosti/log/django.log",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },  # noqa
    },  # noqa
}

# Email
# https://docs.djangoproject.com/en/3.2/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.science.ru.nl"
EMAIL_PORT = 25
EMAIL_DEFAULT_SENDER = "www-tosti@science.ru.nl"
EMAIL_HOST_USER = "www-tosti@science.ru.nl"
DEFAULT_FROM_EMAIL = "TOSTI <www-tosti@science.ru.nl>"
SERVER_EMAIL = "www-tosti@science.ru.nl"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = Path("/tosti/static/")
STATIC_URL = "/static/"

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

MEDIA_ROOT = Path("/tosti/media/")
MEDIA_URL = "/media/"

# MUSIC PLAYERS
SPOTIFY_CACHE_PATH = Path("/tosti/cache/spotipycache/")
MARIETJE_CACHE_PATH = Path("/tosti/cache/marietjecache/")

# SENTRY
sentry_sdk.init(
    dsn=os.environ.get("DJANGO_SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
)

# CACHES
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": Path("/tosti/cache/cache/"),
    }
}

# YIVI
YIVI_SERVER = os.environ.get("DJANGO_YIVI_SERVER")
YIVI_TOKEN = os.environ.get("DJANGO_YIVI_TOKEN")

# SAML SP SETTINGS
SAML_SESSION_COOKIE_NAME = "saml_session"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SAML_USE_NAME_ID_AS_USERNAME = False
SAML_ATTRIBUTE_MAPPING = {
    "uid": ("username",),
    "mail": ("email",),
    "displayName": ("full_name",),
}
SAML_CONFIG = {
    "xmlsec_binary": "/usr/bin/xmlsec1",
    "entityid": "tosti.science.ru.nl",
    "allow_unknown_attributes": True,
    "service": {
        "sp": {
            "name": "TOSTI",
            "name_id_format": saml.NAMEID_FORMAT_PERSISTENT,
            "endpoints": {
                "assertion_consumer_service": [
                    (f"https://tosti.science.ru.nl/saml/acs/", saml2.BINDING_HTTP_POST),
                    (
                        f"https://tosti.science.ru.nl/sso/science/acs/",
                        saml2.BINDING_HTTP_POST,
                    ),  # Legacy, remove when possible
                ],
                "single_logout_service": [
                    (f"https://tosti.science.ru.nl/saml/ls/", saml2.BINDING_HTTP_REDIRECT),
                    (f"https://tosti.science.ru.nl/saml/ls/post", saml2.BINDING_HTTP_POST),
                    (
                        f"https://tosti.science.ru.nl/sso/science/slo/",
                        saml2.BINDING_HTTP_REDIRECT,
                    ),  # Legacy, remove when possible
                    (
                        f"https://tosti.science.ru.nl/sso/science/slo/post",
                        saml2.BINDING_HTTP_POST,
                    ),  # Legacy, remove when possible
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
            "/tosti/saml/metadata.xml",
        ],
    },
    "debug": 1,
    "key_file": "/tosti/saml/private.key",
    "cert_file": "/tosti/saml/public.cert",
    "encryption_keypairs": [
        {
            "key_file": "/tosti/saml/private.key",
            "cert_file": "/tosti/saml/public.cert",
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
            ("https://tosti.science.ru.nl", "nl"),
            ("https://tosti.science.ru.nl", "en"),
        ],
    },
}
