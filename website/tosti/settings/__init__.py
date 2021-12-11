import logging
import os

if os.environ.get("DOCUTILSCONFIG"):
    # Load all default settings because we need to use settings.configure
    # for sphinx documentation generation.
    from django.conf.global_settings import *

# Load base settings
from . import base

logger = logging.getLogger(__name__)

# Attempt to load local overrides
try:
    from .localsettings import *
except ImportError:
    pass

# Load production settings if DJANGO_PRODUCTION is set
if os.environ.get("DJANGO_PRODUCTION"):
    from . import production