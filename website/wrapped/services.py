from itertools import cycle
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone

from wrapped.periods import current_period, tracked_since
from wrapped.personal import personal_wrapped
from wrapped.slides import SLIDE_GENERATORS

SEEN_COOKIE = "tosti-wrapped-seen"
SHARE_LINES = 5
COMMUNITY_THEMES = ["toast", "night", "cheese", "berry"]


def is_available(period):
    """Return whether the Wrapped of a period can be viewed: once it is over, or while it is being shown."""
    return period.end < timezone.localdate() or period == current_period()


def _format(value):
    return f"{value:,}" if isinstance(value, int) else str(value)


def _format_slides(slides):
    for slide in slides:
        slide["count_to"] = slide["value"] if isinstance(slide["value"], int) else None
        slide["value"] = _format(slide["value"])
        for item in slide.get("ranking", []):
            item["value"] = _format(item["value"])
    return slides


def _format_share(lines):
    return [
        {"label": line["label"], "value": _format(line["value"])}
        for line in lines[:SHARE_LINES]
    ]


def collect_slides(period):
    """Collect all community Wrapped slides for a period."""
    return _format_slides(
        [slide for generator in SLIDE_GENERATORS for slide in generator(period)]
    )


def get_slides(period):
    """Get the (cached) community Wrapped slides for a period."""
    # A period that is still going on changes, past ones are final.
    timeout = 60 * 60 if period.is_ongoing() else 60 * 60 * 24
    return cache.get_or_set(
        f"wrapped:slides:{period.start}", lambda: collect_slides(period), timeout
    )


def get_story(user, period):
    """
    Get everything to show the Wrapped of a period to a user.

    Personal slides are never cached nor shown to anyone else than the user they are about.
    """
    community = get_slides(period)
    personal = personal_wrapped(user, period)
    personal_slides = _format_slides(personal["slides"])

    if personal["share"]:
        share_title, share_lines = "My TOSTI Wrapped", personal["share"]
    else:
        share_title, share_lines = "TOSTI Wrapped", [
            slide["share"] for slide in community if "share" in slide
        ]

    # Mix personal and community slides into one story. Personal slides get their own colour, so it's clear which
    # ones are about you; the community slides cycle through the others.
    community_themes = cycle(COMMUNITY_THEMES)
    slides = sorted(
        [{**slide, "theme": "personal"} for slide in personal_slides]
        + [{**slide, "theme": next(community_themes)} for slide in community],
        key=lambda slide: slide["order"],
    )

    return {
        "period": period,
        "slides": slides,
        "personal_slides": personal_slides,
        "personal_partial": personal["partial"],
        "personal_since": (
            tracked_since(period) if personal["partial"] and personal_slides else None
        ),
        "community_slides": community,
        "has_slides": bool(personal_slides or community),
        "share": {
            "title": share_title,
            "year": period.label,
            "lines": _format_share(share_lines),
            "art": static(personal["art"]) if personal.get("art") else None,
            "logo": static("tosti/favicon/android-chrome-512x512.png"),
            "footer": urlparse(
                getattr(settings, "TOSTI_CANONICAL_URL", "https://tosti.science.ru.nl")
            ).netloc,
        },
    }


def render_popup(request):
    """
    Render the Wrapped popup for a request, or return None if there is nothing to show.

    The popup is empty until it is opened: its slides are then loaded from ``StoryView``, so pages don't have to
    compute anything. Until the user has seen this period's Wrapped, a small invitation offers to open it.
    """
    period = current_period()
    if period is None or not request.user.is_authenticated or not get_slides(period):
        return None

    return render_to_string(
        "wrapped/popup.html",
        {
            "period": period,
            "seen_cookie": SEEN_COOKIE,
            "invite": request.COOKIES.get(SEEN_COOKIE) != str(period.start),
        },
        request=request,
    )
