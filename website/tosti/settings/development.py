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

# Yivi settings
YIVI_SERVER = "https://yivi.larsvanrhijn.nl"
YIVI_TOKEN = "test-token-tosti"
