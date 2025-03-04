import time
from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext as _
from django.template.defaultfilters import pluralize


def humanize_duration(duration: timedelta) -> str:
    """
    Get a humanized string representing time difference.

    For example: 2 days 1 hour 25 minutes 10 seconds.
    """
    days = duration.days
    hours = int(duration.seconds / 3600)
    minutes = int(duration.seconds % 3600 / 60)
    seconds = int(duration.seconds % 3600 % 60)

    parts = []
    if days > 0:
        parts.append("{} {}".format(days, pluralize(days, _("day,days"))))

    if hours > 0:
        parts.append("{} {}".format(hours, pluralize(hours, _("hour,hours"))))

    if minutes > 0:
        parts.append("{} {}".format(minutes, pluralize(minutes, _("minute,minutes"))))

    if seconds > 0:
        parts.append("{} {}".format(seconds, pluralize(seconds, _("second,seconds"))))

    return ", ".join(parts) if len(parts) != 0 else _("< 1 second")


def get_class(kls):
    """Convert a string to a class."""
    parts = kls.split(".")

    if len(parts) == 1:
        raise ImportError("'{0}'' is not a valid import path".format(kls))

    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def get_current_timezone_offset() -> timedelta:
    """Get the offset from the default timezone."""
    return timezone.localtime(timezone.now()).utcoffset()


def run_at_time_localized(run_at_time: str) -> str:
    """Get the localized run_at_times."""
    timezone_offset_minutes = get_current_timezone_offset().seconds / 60
    timezone_offset_hours = timezone_offset_minutes // 60
    timezone_offset_minutes = timezone_offset_minutes % 60
    interpreted_time = time.strptime(run_at_time, "%H:%M")
    localized_time_hours = int((interpreted_time.tm_hour + timezone_offset_hours) % 24)
    localized_time_minutes = int((interpreted_time.tm_min + timezone_offset_minutes) % 60)
    return f"{localized_time_hours:02d}:{localized_time_minutes:02d}"
