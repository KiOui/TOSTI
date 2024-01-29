import os

from .base import *

import saml2
from saml2 import saml, xmldsig

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

SESSION_COOKIE_SECURE = True


# Databases
# https://docs.djangoproject.com/en/3.2/ref/databases/

from .base import *  # noqa

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": os.environ.get("POSTGRES_PORT"),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATIC_URL = os.environ.get("DJANGO_STATIC_URL")
MEDIA_URL = os.environ.get("DJANGO_MEDIA_URL")

STATIC_ROOT = os.environ.get("DJANGO_STATIC_ROOT")
MEDIA_ROOT = os.environ.get("DJANGO_MEDIA_ROOT")


# Logging
# https://docs.djangoproject.com/en/3.2/topics/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "/var/log/django.log",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}


# Email
# https://docs.djangoproject.com/en/3.2/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_DEFAULT_SENDER = os.environ.get("EMAIL_DEFAULT_SENDER")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL")


# SPOTIFY
SPOTIFY_CACHE_PATH = BASE_DIR.parent.parent / "cache" / "spotipycache"
MARIETJE_CACHE_PATH = BASE_DIR.parent.parent / "cache" / "marietjecache"

# SENTRY
if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

# CACHES
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR.parent.parent / "cache" / "cache",
    }
}

# SAML SP SETTINGS
SAML_SESSION_COOKIE_NAME = "saml_session"
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SAML_USE_NAME_ID_AS_USERNAME = False
SAML_ATTRIBUTE_MAPPING = {
    "uid": ("username",),
    "mail": ("email",),
    "displayName": ("full_name",),
}
SAML_CONFIG = {
    "xmlsec_binary": "/usr/bin/xmlsec1",
    "entityid": os.environ.get("SAML_ENTITY_ID"),
    "allow_unknown_attributes": True,
    "service": {
        "sp": {
            "name": "TOSTI",
            "name_id_format": saml.NAMEID_FORMAT_PERSISTENT,
            "endpoints": {
                "assertion_consumer_service": [
                    (f"{os.environ.get('SAML_BASE_URL')}/saml/acs/", saml2.BINDING_HTTP_POST),
                    (
                        f"{os.environ.get('SAML_BASE_URL')}/sso/science/acs/",
                        saml2.BINDING_HTTP_POST,
                    ),  # Legacy, remove when possible
                ],
                "single_logout_service": [
                    (f"{os.environ.get('SAML_BASE_URL')}/saml/ls/", saml2.BINDING_HTTP_REDIRECT),
                    (f"{os.environ.get('SAML_BASE_URL')}/saml/ls/post", saml2.BINDING_HTTP_POST),
                    (
                        f"{os.environ.get('SAML_BASE_URL')}/sso/science/slo/",
                        saml2.BINDING_HTTP_REDIRECT,
                    ),  # Legacy, remove when possible
                    (
                        f"{os.environ.get('SAML_BASE_URL')}/sso/science/slo/post",
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
            os.path.join(BASE_DIR, "tosti", "settings", "saml", "metadata.xml"),
        ],
    },
    "debug": 1,
    "key_file": os.path.join(BASE_DIR, "tosti", "settings", "saml", "private.key"),
    "cert_file": os.path.join(BASE_DIR, "tosti", "settings", "saml", "public.cert"),
    "encryption_keypairs": [
        {
            "key_file": os.path.join(BASE_DIR, "tosti", "settings", "saml", "private.key"),
            "cert_file": os.path.join(BASE_DIR, "tosti", "settings", "saml", "public.cert"),
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
