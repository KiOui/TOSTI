import os

from .base import *

SECRET_KEY = "django-insecure-7c^z*je^r!@aw!0*vuc1t4cp1rfi+4+xu@x5pva@xc@rf%3#lt"

DEBUG = True

ALLOWED_HOSTS = []


# Databases
# https://docs.djangoproject.com/en/3.2/ref/databases/

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Cors configuration
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(?:api|user/oauth)/.*"

# OAuth configuration
OAUTH2_PROVIDER["ALLOWED_REDIRECT_URI_SCHEMES"] = ["http", "https", "nu.thalia"]
# Allow http://localhost redirect URIs so MCP clients bootstrapped in dev can
# come back via the standard OAuth 2.1 loopback exemption.
OAUTH2_PROVIDER["ALLOW_LOCALHOST_LOOPBACK"] = True
# Dev intentionally allows plaintext http redirect URIs for native-app loopback
# testing (per RFC 8252). Downgrade the RFC 9700 §2.1 deploy-check gate back to
# a warning so ``manage.py check --deploy`` doesn't fail with an error the
# override is already handling correctly.
OAUTH2_PROVIDER["COMPLIANT_BCP_RFC9700_REDIRECT_URI_SCHEME"] = False

# MCP serverInfo icons are built relative to this base — point at the local
# dev server so a connector added in dev shows the right icons.
TOSTI_CANONICAL_URL = "http://127.0.0.1:8000"
# Keep the OAuth2 discovery issuer aligned with the dev-server URL so metadata,
# RFC 9207 ``iss`` values, and the RFC 9728 authorization_servers list agree.
OAUTH2_PROVIDER["OIDC_ISS_ENDPOINT"] = TOSTI_CANONICAL_URL

# Email
# https://docs.djangoproject.com/en/3.2/topics/email/

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_DEFAULT_SENDER = "development@example.com"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = BASE_DIR / "static"
STATIC_URL = "/static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# SPOTIFY SETTINGS
SPOTIFY_CACHE_PATH = os.path.join(BASE_DIR, "cache/spotify")  # noqa
MARIETJE_CACHE_PATH = os.path.join(BASE_DIR, "cache/marietje")  # noqa

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Celery will execute tasks in the same process instead of sending it to a Redis server.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
