"""
The personal slides of TOSTI Wrapped.

These are only ever shown to the user they are about. They use the same slide format as ``wrapped.slides``, plus
``tags`` (a list of short strings) on the personality slide.

When only part of the period is still linked to users (see ``tracked_since``), every personal number says from when
it counts (e.g. "since September"), so it isn't mistaken for a total of the whole period. Periods starting before
``WRAPPED_PERSONAL_FROM`` only get the personality slide, with a footnote saying since when it counts.
"""

import datetime
import math
from collections import Counter

from constance import config
from django.db.models import Count
from django.template.defaultfilters import pluralize
from django.utils import timezone

from orders.models import Order, Shift
from thaliedje.models import SpotifyQueueItem
from wrapped.periods import longest_streak, tracked_since, week
from wrapped.personality import features, period_context, personality, queue_positions
from wrapped.slides import (
    TOSTI_HEIGHT_METRES,
    artist_names,
    canteen_name,
    times,
    top_artists,
    top_tracks,
    tosti_tower,
    tower_illustration,
)

# Only brag about being in the top X% when X is at most this.
TOP_PERCENTAGE_THRESHOLD = 25

# Heights to compare someone's tosti tower with.
GIRAFFE_METRES = 5
PERSON_METRES = 2

# How many months of the visit calendar to show per row, on small and large screens.
CALENDAR_COLUMNS = 4
CALENDAR_COLUMNS_LARGE = 6

# How many people to draw in the queue illustration.
QUEUE_LENGTH = 7


def top_percentage(queryset, user_field, amount):
    """Return in which top percentage of users someone with ``amount`` rows in ``queryset`` is."""
    per_user = (
        queryset.filter(**{f"{user_field}__isnull": False})
        .values(user_field)
        .annotate(amount=Count("id"))
    )
    users = per_user.count()
    if users == 0:
        return 100
    return math.ceil(100 * (per_user.filter(amount__gt=amount).count() + 1) / users)


def queue_stats(positions):
    """
    Return where someone usually was in the queue, from their ``(position, number of orders)`` in every shift.

    :return: None if they didn't order, otherwise a dict with the ``average`` position (1 is first), the ``relative``
    average position (0 is first, 1 is last) and how often they were ``first`` in line.
    """
    if not positions:
        return None
    return {
        "average": sum(position for position, _ in positions) / len(positions),
        "relative": sum(
            (position - 1) / max(size - 1, 1) for position, size in positions
        )
        / len(positions),
        "first": sum(1 for position, _ in positions if position == 1),
    }


def _weekday_name(weekday):
    """Return the name of a ``date.weekday()`` (0 is Monday)."""
    return datetime.date(2024, 1, 1 + weekday).strftime(
        "%A"
    )  # 1 January 2024 was a Monday.


def queue_illustration(relative_position):
    """Return what to draw for someone's usual spot in the queue: a short queue with them in it."""
    you = round(relative_position * (QUEUE_LENGTH - 1))
    return {
        "type": "queue",
        "people": [{"you": index == you} for index in range(QUEUE_LENGTH)],
    }


def _days(amount):
    return f"{amount:,} day{pluralize(amount)}"


def _join(words):
    """Join words like 'Mondays, Tuesdays and Wednesdays'."""
    words = list(words)
    return words[0] if len(words) == 1 else f"{', '.join(words[:-1])} and {words[-1]}"


def visit_calendar(visits, days_open, first_day, last_day):
    """
    Return a calendar of the months from ``first_day`` to ``last_day``, marking which days someone came by.

    :return: list of months with a ``name``, ``blanks`` (empty cells before the 1st, weeks start on Monday) and
    ``days``, each with a ``state``: visited, open (the canteen was open), closed or outside (not in the period).
    """
    months = []
    month = first_day.replace(day=1)
    while month <= last_day:
        days = []
        day = month
        while day.month == month.month:
            if day < first_day or day > last_day:
                state = "outside"
            elif day in visits:
                state = "visited"
            elif day in days_open:
                state = "open"
            else:
                state = "closed"
            days.append({"day": day.day, "state": state})
            day += datetime.timedelta(days=1)
        months.append(
            {"name": f"{month:%B}", "blanks": range(month.weekday()), "days": days}
        )
        month = day
    return months


def _bragging(percentage, what):
    if percentage > TOP_PERCENTAGE_THRESHOLD:
        return ""
    return f" That puts you in the top {percentage}% of {what}!"


def baker_slide(user, period):
    """Return the slide about the shifts someone was a baker in, or None if they weren't."""
    shifts = period.filter(Shift.objects.filter(assignees=user), "start")
    days = [
        timezone.localtime(start).date()
        for start in shifts.values_list("start", flat=True)
    ]
    if not days:
        return None
    tostis = Order.objects.filter(
        shift__in=shifts, product__name__icontains="tosti"
    ).count()
    weekdays = Counter(day.weekday() for day in days)
    most = max(weekdays.values())
    favourites = [
        _weekday_name(weekday) for weekday in range(7) if weekdays[weekday] == most
    ]
    text = f"shift{pluralize(len(days))} you were a baker, mostly on {_join(f'{day}s' for day in favourites)}."
    if tostis:
        text += f" Together with your fellow bakers, you grilled {tostis:,} tosti{pluralize(tostis)}. Thank you!"
    else:
        text += " Thank you!"
    return {
        "kicker": "Behind the counter",
        "icon": "fa-fire-burner",
        "icon_animation": "flicker",
        "order": 52,
        "value": len(days),
        "text": text,
        "bars": [
            {
                "label": _weekday_name(weekday)[:3],
                "height": round(100 * weekdays[weekday] / most),
                "top": weekdays[weekday] == most,
            }
            for weekday in range(7)
            if weekday < 5 or weekdays[weekday]
        ],
        "share": {"label": "Shifts as a baker", "value": len(days)},
    }


def personal_wrapped(user, period):
    """
    Return the personal Wrapped of a user for a period.

    :return: dict with ``slides``, ``share`` (lines for the share image, the personality comes first) and
    ``partial`` (whether only part of the period is known, in which case every number says since when).
    """
    personality_only = period.start < config.WRAPPED_PERSONAL_FROM
    since = tracked_since(period)

    def counted(queryset, field):
        """Filter a queryset on what personal statistics count: the period, from ``since``."""
        queryset = period.filter(queryset, field)
        return (
            queryset
            if since is None
            else queryset.filter(**{f"{field}__date__gte": since})
        )

    # Shifts aren't anonymised, so the baker slide always covers the whole period.
    baker = baker_slide(user, period)
    bakers = [baker] if baker else []

    orders = counted(Order.objects.filter(user=user), "created")
    requests = counted(SpotifyQueueItem.objects.filter(requested_by=user), "added")
    order_rows = list(
        orders.values_list("created", "product__name", "shift__venue__venue__name")
    )
    request_times = list(requests.values_list("added", flat=True))

    order_days = {timezone.localtime(created).date() for created, _, _ in order_rows}
    song_days = {timezone.localtime(added).date() for added in request_times}
    # A visit is a day you ordered something or requested a song (or both).
    visits = order_days | song_days
    if not visits:
        return {
            "slides": bakers,
            "share": [slide["share"] for slide in bakers],
            "partial": since is not None and not personality_only,
        }

    context = period_context(period, since)
    days_open = context["open_days"]
    weeks_open = context["open_weeks"]
    weeks = {week(day) for day in visits}
    products = Counter(name for _, name, _ in order_rows)
    canteens = Counter(canteen_name(canteen) for _, _, canteen in order_rows)
    positions = [
        position
        for (order_user, _), position in queue_positions(orders).items()
        if order_user == user.pk
    ]
    queue = queue_stats(positions)
    weekdays = Counter(day.weekday() for day in visits)
    suffix = f" since {since:%B}" if since is not None else ""

    you = personality(
        features(order_rows, request_times, positions, context), period, since, suffix
    )
    calendar = visit_calendar(
        visits,
        set(days_open),
        since or period.start,
        period.last_day,
    )
    personality_slide = {
        "kicker": "Your TOSTI personality",
        "order": 100,
        "value": you["name"],
        "text": you["description"],
        "tags": you["tags"],
        "calendar": calendar,
        # Months per row on small and large screens.
        "calendar_columns": min(len(calendar), CALENDAR_COLUMNS),
        "calendar_columns_large": min(len(calendar), CALENDAR_COLUMNS_LARGE),
    }
    share = [{"label": "TOSTI personality", "value": you["name"]}]
    if you["tags"]:
        share.append({"label": "Known for", "value": " · ".join(you["tags"])})

    if personality_only:
        if since is not None:
            personality_slide["footnote"] = (
                f"Based on your visits since {since.day} {since:%B} only: due to data minimisation, TOSTI no "
                "longer knows who ordered what before then, so we can't look back at your whole year."
            )
        slides = [personality_slide] + bakers
        return {
            "slides": slides,
            "share": share + [slide["share"] for slide in bakers],
            "partial": False,
        }

    partial = since is not None
    slides = [
        {
            "kicker": "Your visits",
            "icon": "fa-calendar-check",
            "icon_animation": "pop",
            "order": 22,
            "value": len(visits),
            "text": f"day{pluralize(len(visits))} you came by{suffix}, out of the {len(days_open):,} days the canteen "
            "was open."
            + _bragging(
                top_percentage(
                    counted(Order.objects.all(), "created"),
                    "user",
                    len(order_rows),
                ),
                f"canteen regulars{suffix}",
            ),
            "share": {"label": f"Days in the canteen{suffix}", "value": len(visits)},
        }
    ]
    # Explain how the visits are counted.
    if song_days:
        slides[0]["ranking"] = [
            {"label": "Days you ordered", "value": _days(len(order_days))},
            {"label": "Days you requested a song", "value": _days(len(song_days))},
        ]
        if order_days & song_days:
            slides[0]["text"] += " Days you did both only count once."
    else:
        slides[0]["text"] += " That's every day you ordered something."

    streak = longest_streak(weeks, weeks_open)
    if streak >= 2:
        slides.append(
            {
                "kicker": "Your streak",
                "icon": "fa-fire",
                "icon_animation": "flicker",
                "order": 23,
                "value": f"{streak} weeks",
                "text": f"in a row you came by at least once{suffix}. Consistency!",
            }
        )

    if len(visits) >= 2:
        most = max(weekdays.values())
        favourites = [
            _weekday_name(weekday) for weekday in range(7) if weekdays[weekday] == most
        ]
        slides.append(
            {
                "kicker": "Your favourite day",
                "order": 31,
                "value": " & ".join(favourites),
                "text": f"You mostly came by on {_join(f'{day}s' for day in favourites)}{suffix}.",
                "bars": [
                    {
                        "label": _weekday_name(weekday)[:3],
                        "height": round(100 * weekdays[weekday] / most),
                        "top": weekdays[weekday] == most,
                    }
                    # Only show the weekend if someone actually came by then.
                    for weekday in range(7)
                    if weekday < 5 or weekdays[weekday]
                ],
            }
        )

    if canteens:
        (canteen, amount), total = canteens.most_common(1)[0], sum(canteens.values())
        if len(canteens) == 1:
            text = f"is your canteen: all your orders{suffix} were placed there."
        else:
            text = f"is your canteen: {round(100 * amount / total)}% of your orders{suffix} were placed there."
        slides.append(
            {
                "kicker": "Your canteen",
                "icon": "fa-location-dot",
                "icon_animation": "bounce",
                "order": 25,
                "value": canteen,
                "text": text,
                "ranking": [
                    {"label": name, "value": times(count)}
                    for name, count in canteens.most_common()
                ],
            }
        )

    if products:
        (top, top_amount), total = products.most_common(1)[0], sum(products.values())
        if len(products) == 1:
            text = f"Every single time{suffix}."
        else:
            text = f"made up {round(100 * top_amount / total)}% of your {total:,} orders{suffix}."
        slides.append(
            {
                "kicker": "Your order",
                "icon": "fa-cheese",
                "icon_animation": "pop",
                "order": 41,
                "value": top,
                "text": text,
                "ranking": [
                    {"label": product, "value": times(amount)}
                    for product, amount in products.most_common(5)
                ],
                "share": {"label": "Favourite", "value": top},
            }
        )

    tostis = sum(
        amount for product, amount in products.items() if "tosti" in product.lower()
    )
    if tostis:
        height = tostis * TOSTI_HEIGHT_METRES
        if height >= GIRAFFE_METRES:
            comparison = " That's taller than a giraffe!"
        elif height >= PERSON_METRES:
            comparison = " That's taller than you are!"
        else:
            comparison = ""
        slides.append(
            {
                "kicker": "Your tosti tower",
                "order": 42,
                "value": tosti_tower(tostis),
                "illustration": tower_illustration(tostis),
                "text": f"is how high your {tostis:,} tosti{pluralize(tostis)}{suffix} would be, stacked on top of "
                f"each other.{comparison}",
            }
        )

    if queue:
        first = (
            f" You were first in line {queue['first']} time{pluralize(queue['first'])}!"
            if queue["first"]
            else ""
        )
        slides.append(
            {
                "kicker": "Your spot in line",
                "order": 51,
                "value": f"#{round(queue['average'])}",
                "illustration": queue_illustration(queue["relative"]),
                "text": f"was your average spot in the queue{suffix}.{first}",
                "share": {
                    "label": f"Average spot in line{suffix}",
                    "value": f"#{round(queue['average'])}",
                },
            }
        )

    if request_times:
        song_count = len(request_times)
        slide = {
            "kicker": "Your soundtrack",
            "icon": "fa-headphones",
            "icon_animation": "bounce",
            "order": 61,
            "value": song_count,
            "text": f"song{pluralize(song_count)} you requested on Thaliedje{suffix}."
            + _bragging(
                top_percentage(
                    counted(SpotifyQueueItem.objects.all(), "added"),
                    "requested_by",
                    song_count,
                ),
                f"Thaliedje DJs{suffix}",
            ),
        }
        tracks = top_tracks(requests, limit=3)
        if tracks:
            slide["ranking"] = [
                {
                    "label": f"{track.track_name} – {artist_names(track)}",
                    "value": times(track.amount),
                }
                for track in tracks
            ]
            slide["share"] = {
                "label": "Top song",
                "value": f"{tracks[0].track_name} – {artist_names(tracks[0])}",
            }
        slides.append(slide)

        artists = top_artists(requests, limit=1)
        if artists:
            slides.append(
                {
                    "kicker": "Your top artist",
                    "icon": "fa-microphone",
                    "icon_animation": "wave",
                    "order": 63,
                    "value": artists[0].artist_name,
                    "text": f"was your most requested artist{suffix}, {artists[0].amount:,} "
                    f"time{pluralize(artists[0].amount)}.",
                }
            )

    slides += bakers
    slides.append(personality_slide)
    return {
        "slides": slides,
        "share": share + [slide["share"] for slide in slides if "share" in slide],
        "partial": partial,
    }
