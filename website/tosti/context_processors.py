import os
import subprocess
from functools import lru_cache

from constance import config
from django.conf import settings

from age.services import get_minimum_age


@lru_cache(maxsize=1)
def _get_commit_sha():
    sha = os.environ.get("SENTRY_RELEASE")
    if sha:
        return sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=settings.BASE_DIR,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except subprocess.CalledProcessError, FileNotFoundError, OSError:
        return None


def footer_credits(request):
    """Get the footer credits as string."""
    sha = _get_commit_sha()
    return {
        "FOOTER_CREDITS_TEXT": config.FOOTER_CREDITS_TEXT,
        "COMMIT_SHA": sha,
        "COMMIT_SHA_SHORT": sha[:7] if sha else None,
    }


def minimum_registered_age(request):
    """Context processor to check if the user has a minimum registered age."""
    if not request.user.is_authenticated:
        return {"minimum_registered_age": False}

    age = get_minimum_age(request.user)
    return {"minimum_registered_age": age is not None}
