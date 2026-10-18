"""
The period TOSTI Wrapped looks back at.

That's a calendar year (e.g. 2026) or a lecture year (e.g. 2026/2027, from September until August), depending on the
``WRAPPED_YEAR_START_MONTH`` setting. Wrapped is shown between ``WRAPPED_SHOW_FROM`` and ``WRAPPED_SHOW_UNTIL``, and
looks back at the year the first of those days falls in.
"""

import datetime
from dataclasses import dataclass

from constance import config
from django.core.cache import cache
from django.db.models import Min
from django.db.models.functions import TruncDate
from django.utils import timezone

from orders.models import Order, Shift
from thaliedje.models import SpotifyQueueItem

# During the first month, we consider the personal statistics to cover the whole period.
WHOLE_PERIOD_GRACE = datetime.timedelta(days=31)


@dataclass(frozen=True)
class Period:
    """A year that Wrapped looks back at, from ``start`` until ``end`` (both included)."""

    start: datetime.date
    end: datetime.date

    @classmethod
    def starting_in(cls, year):
        """Return the period that starts in a year, e.g. the lecture year 2026/2027 for 2026."""
        month = config.WRAPPED_YEAR_START_MONTH
        return cls(
            datetime.date(year, month, 1),
            datetime.date(year + 1, month, 1) - datetime.timedelta(days=1),
        )

    @classmethod
    def containing(cls, day):
        """Return the period a day falls in."""
        period = cls.starting_in(day.year)
        return period if day >= period.start else cls.starting_in(day.year - 1)

    @property
    def label(self):
        """Return how to call the period, e.g. '2026' or '2026/2027'."""
        if self.start.year == self.end.year:
            return str(self.start.year)
        return f"{self.start.year}/{self.end.year}"

    @property
    def last_day(self):
        """Return the last day there can be data of: the end of the period, or today if it hasn't ended yet."""
        return min(self.end, timezone.localdate())

    def is_ongoing(self):
        """Return whether today falls in the period."""
        return self.start <= timezone.localdate() <= self.end

    def filter(self, queryset, field):
        """Filter a queryset on a date(time) ``field`` falling in the period."""
        return queryset.filter(**{f"{field}__date__range": (self.start, self.end)})

    def __str__(self):
        """Return the label."""
        return self.label


def current_period():
    """Return the period whose Wrapped is shown right now, or None if Wrapped isn't shown."""
    if (
        not config.WRAPPED_SHOW_FROM
        <= timezone.localdate()
        <= config.WRAPPED_SHOW_UNTIL
    ):
        return None
    return Period.containing(config.WRAPPED_SHOW_FROM)


def tracked_since(period):
    """
    Return the date from which personal statistics of a period count, e.g. since orders are still linked to users.

    Older data is anonymised (see the data minimisation of ``orders`` and ``thaliedje``), so personal statistics may
    only cover part of the period. ``WRAPPED_PERSONAL_DATA_SINCE`` can set a later date, when the data before it is
    incomplete. Returns None if they cover (practically) the whole period.
    """
    configured = config.WRAPPED_PERSONAL_DATA_SINCE
    configured = configured if period.start < configured <= period.end else None
    firsts = [
        period.filter(Order.objects.filter(user__isnull=False), "created").aggregate(
            first=Min("created")
        )["first"],
        period.filter(
            SpotifyQueueItem.objects.filter(requested_by__isnull=False), "added"
        ).aggregate(first=Min("added"))["first"],
    ]
    firsts = [first for first in firsts if first is not None]
    if not firsts:
        return configured
    since = timezone.localtime(min(firsts)).date()
    since = since if since > period.start + WHOLE_PERIOD_GRACE else None
    if configured is None:
        return since
    return max(since or configured, configured)


def open_days(period, since=None):
    """Return the sorted days in a period (from ``since``) with an order, song request or shift."""

    def collect():
        days = set()
        for queryset, field in (
            (Order.objects.all(), "created"),
            (SpotifyQueueItem.objects.all(), "added"),
            (Shift.objects.all(), "start"),
        ):
            days |= set(
                period.filter(queryset, field)
                .annotate(day=TruncDate(field))
                .values_list("day", flat=True)
                .distinct()
            )
        return sorted(day for day in days if since is None or day >= since)

    return cache.get_or_set(
        f"wrapped:open-days:{period.start}:{since}", collect, 60 * 60
    )


def week(day):
    """Return the (year, week number) of a day."""
    return day.isocalendar()[:2]


def longest_streak(active, ordered):
    """Return the longest run of consecutive items of ``ordered`` that are all in ``active``."""
    best = current = 0
    for item in ordered:
        current = current + 1 if item in active else 0
        best = max(best, current)
    return best
