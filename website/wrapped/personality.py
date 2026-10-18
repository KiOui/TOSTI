"""
The TOSTI personality of TOSTI Wrapped: what makes someone stand out compared to everyone else.

Every personality belongs to a dimension, e.g. how early in the queue someone usually is. For each dimension someone
qualifies for, we compute their percentile among everyone that qualifies in the period. They get the personality of the
dimension in which they stand out most. To keep the personalities spread about evenly, every personality also gets a
small boost, tuned every period on that period's (anonymous) data.

Only anonymous numbers are cached: per dimension the sorted values of everyone, and the boosts.
"""

import datetime
import re
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict

from django.core.cache import cache
from django.db.models import Count, F, Window
from django.db.models.functions import RowNumber
from django.utils import timezone

from orders.models import Order
from thaliedje.models import SpotifyQueueItem
from wrapped.periods import longest_streak, open_days, week
from wrapped.slides import canteen_name

# Name and description of every personality.
PERSONALITIES = {
    "furniture": (
        "Part of the Furniture",
        "You were in the canteen so often, we started to think you lived there.",
    ),
    "clockwork": (
        "The Clockwork",
        "Week in, week out: we could set our watch by your tosti.",
    ),
    "early": (
        "The Early Bird",
        "First in line while the grill was still warming up.",
    ),
    "late": (
        "The Last-Minute Luncher",
        "Why queue when you can come by once the rush is over?",
    ),
    "hopper": (
        "The Canteen Hopper",
        "North or South? You know your way around both canteens.",
    ),
    "mixer": (
        "The 50/50",
        "Why choose one tosti when you can have them all?",
    ),
    "dj": (
        "The DJ",
        "The canteen is your dance floor: you made sure the music was right.",
    ),
    "binger": (
        "The Binger",
        "When you're in, you're all in: lots of tostis in just a few weeks.",
    ),
    "rare": (
        "The Rare Sighting",
        "We only saw you once or twice. Come by more often, we'll keep the grill warm!",
    ),
}

# What every personality means: what made someone get it.
MEANINGS = {
    "furniture": "You get this personality when you stand out in how many of the days the canteen was open you "
    "came by.",
    "clockwork": "You get this personality when you stand out in coming by week after week, with a long streak of "
    "weeks in a row.",
    "early": "You get this personality when you were usually one of the first to order in a shift.",
    "late": "You get this personality when you usually ordered near the end of a shift, after the rush.",
    "hopper": "You get this personality when you ordered in both canteens, instead of sticking to one.",
    "mixer": "You get this personality when you ordered a mix of products, instead of always the same one.",
    "dj": "You get this personality when you stand out in how many songs you requested on Thaliedje.",
    "binger": "You get this personality when most of your visits fell within just two weeks.",
    "rare": "You get this personality when you came by only once or twice.",
}

# What to say about how someone compares to everyone else, for dimensions where that makes sense.
COMPARISONS = {
    "furniture": "You came by more often than {percentage}% of TOSTI users{period}.",
    "clockwork": "You came by more consistently than {percentage}% of TOSTI users{period}.",
    "early": "You were earlier in line than {percentage}% of TOSTI users{period}.",
    "late": "You were later in line than {percentage}% of TOSTI users{period}.",
    "dj": "You requested more songs than {percentage}% of the Thaliedje DJs{period}.",
}

# Short tags for the other dimensions someone stands out in.
TAGS = {
    "furniture": "Regular",
    "clockwork": "Consistent",
    "early": "Early bird",
    "late": "Fashionably late",
    "hopper": "Canteen hopper",
    "dj": "DJ",
    "binger": "Binger",
}

# Who qualifies for which personality.
RARE_MAX_VISITS = 2
MIX_MAX_SHARE = 2 / 3
DJ_MIN_SONGS = 2
BINGER_MIN_DAYS = 8 * 7
BINGER_MIN_VISITS = 4
BINGER_MIN_SHARE_IN_14_DAYS = 0.6

# Tags.
TAG_MIN_PERCENTILE = 0.75
LOVER_MIN_SHARE = 0.75
TEAM_MIN_SHARE = 0.8

# Tuning the boosts.
TUNING_ROUNDS = 150
TUNING_STEP = 0.01
TUNING_MAX_SHARE_OF_QUALIFIED = 0.9


def product_flavour(name):
    """Return the flavour of a product, e.g. 'Tosti Ham-Cheese' and 'Free tosti ham-cheese for X' are 'ham-cheese'."""
    name = re.sub(r"\bfor\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\b(tosti|free)\b", "", name, flags=re.IGNORECASE)
    return name.strip(" -").lower() or name.lower()


def features(order_rows, request_times, queue_positions, context):
    """
    Return what is needed to determine someone's personality.

    :param order_rows: (created, product name, canteen name) of every order
    :param request_times: when every song was requested
    :param queue_positions: (position, number of orders) of someone's first order in every shift they ordered in
    :param context: the ``context`` of the period (see ``period_context``)
    """
    order_days = {timezone.localtime(created).date() for created, _, _ in order_rows}
    visits = sorted(
        order_days | {timezone.localtime(added).date() for added in request_times}
    )
    if not visits:
        return None
    flavours = Counter(product_flavour(product) for _, product, _ in order_rows)
    canteens = Counter(canteen_name(canteen) for _, _, canteen in order_rows)
    orders = len(order_rows)
    return {
        "visit_days": len(visits),
        "longest_week_streak": longest_streak(
            {week(day) for day in visits}, context["open_weeks"]
        ),
        "max_visits_in_14_days": max(
            sum(
                1
                for day in visits
                if start <= day < start + datetime.timedelta(days=14)
            )
            for start in visits
        ),
        "orders": orders,
        "flavours": flavours,
        "top_product_share": flavours.most_common(1)[0][1] / orders if orders else None,
        "products": len(flavours),
        "canteens": canteens,
        "top_canteen_share": canteens.most_common(1)[0][1] / orders if orders else None,
        "queue_shifts": len(queue_positions),
        "queue_relative": (
            sum((position - 1) / max(size - 1, 1) for position, size in queue_positions)
            / len(queue_positions)
            if queue_positions
            else None
        ),
        "queue_first": sum(1 for position, _ in queue_positions if position == 1),
        "songs": len(request_times),
    }


# For every personality: who qualifies, and how much they stand out (higher is more).
DIMENSIONS = {
    "furniture": (
        lambda f, c: f["visit_days"] > RARE_MAX_VISITS,
        lambda f, c: f["visit_days"] / max(len(c["open_days"]), 1),
    ),
    "clockwork": (
        lambda f, c: f["visit_days"] > RARE_MAX_VISITS,
        lambda f, c: f["longest_week_streak"] / max(len(c["open_weeks"]), 1),
    ),
    "early": (lambda f, c: f["queue_shifts"] > 0, lambda f, c: -f["queue_relative"]),
    "late": (lambda f, c: f["queue_shifts"] > 0, lambda f, c: f["queue_relative"]),
    "hopper": (
        lambda f, c: f["orders"] >= 2 and f["top_canteen_share"] <= MIX_MAX_SHARE,
        lambda f, c: 1 - f["top_canteen_share"],
    ),
    "mixer": (
        lambda f, c: f["orders"] >= 2 and f["top_product_share"] <= MIX_MAX_SHARE,
        lambda f, c: 1 - f["top_product_share"],
    ),
    "dj": (lambda f, c: f["songs"] >= DJ_MIN_SONGS, lambda f, c: f["songs"]),
    "binger": (
        lambda f, c: c["days"] >= BINGER_MIN_DAYS
        and f["visit_days"] >= BINGER_MIN_VISITS
        and f["max_visits_in_14_days"] / f["visit_days"] >= BINGER_MIN_SHARE_IN_14_DAYS,
        lambda f, c: f["max_visits_in_14_days"] / f["visit_days"],
    ),
    "rare": (
        lambda f, c: f["visit_days"] <= RARE_MAX_VISITS,
        lambda f, c: -f["visit_days"],
    ),
}


def period_context(period, since):
    """Return the open days and weeks of the period personal statistics cover."""
    days = open_days(period, since)
    first = since or period.start
    last = period.last_day
    return {
        "open_days": days,
        "open_weeks": sorted({week(day) for day in days}),
        "days": (last - first).days + 1,
    }


def queue_positions(orders):
    """Return, per (user, shift), the (position, number of orders) of the user's first order in that shift."""
    positions = {}
    for user, shift, position, size in (
        Order.objects.filter(shift__in=orders.values("shift"))
        .annotate(
            position=Window(
                RowNumber(),
                partition_by=[F("shift")],
                order_by=[F("created").asc(), F("pk").asc()],
            ),
            shift_size=Window(Count("id"), partition_by=[F("shift")]),
        )
        .values_list("user", "shift", "position", "shift_size")
    ):
        if user is not None and (
            (user, shift) not in positions or position < positions[(user, shift)][0]
        ):
            positions[(user, shift)] = (position, size)
    return positions


def everyones_features(period, since, context):
    """Return the features of everyone with (still linked) orders or song requests in a period, without who it is."""
    orders = period.filter(Order.objects.filter(user__isnull=False), "created")
    requests = period.filter(
        SpotifyQueueItem.objects.filter(requested_by__isnull=False), "added"
    )
    if since is not None:
        orders = orders.filter(created__date__gte=since)
        requests = requests.filter(added__date__gte=since)

    order_rows = defaultdict(list)
    for user, created, product, canteen in orders.values_list(
        "user", "created", "product__name", "shift__venue__venue__name"
    ):
        order_rows[user].append((created, product, canteen))
    request_times = defaultdict(list)
    for user, added in requests.values_list("requested_by", "added"):
        request_times[user].append(added)
    positions = defaultdict(list)
    for (user, _), position in queue_positions(orders).items():
        positions[user].append(position)

    return [
        features(order_rows[user], request_times[user], positions[user], context)
        for user in set(order_rows) | set(request_times)
    ]


def tune(everyone, context):
    """
    Return the populations per dimension, and the boosts that spread the personalities about evenly.

    Everyone gets the personality where (percentile + boost) is highest. The boosts are tuned so every personality
    gets about the same number of people (see ``_even_goals``).
    """
    populations = {
        key: sorted(value(f, context) for f in everyone if qualifies(f, context))
        for key, (qualifies, value) in DIMENSIONS.items()
    }
    percentiles = [standing_out(f, populations, context) for f in everyone]
    boosts = {key: 0.0 for key in DIMENSIONS}
    if not everyone:
        return populations, boosts

    goals = _even_goals(
        len(everyone), {key: len(populations[key]) for key in DIMENSIONS}
    )
    scale = len(everyone) / len(DIMENSIONS)
    for _ in range(TUNING_ROUNDS):
        counts = Counter(_best(p, boosts) for p in percentiles if p)
        for key in DIMENSIONS:
            boosts[key] += TUNING_STEP * (goals[key] - counts[key]) / scale
    # Only the differences between boosts matter; keep them around zero so they are easy to read.
    average = sum(boosts.values()) / len(boosts)
    boosts = {key: boost - average for key, boost in boosts.items()}
    return populations, boosts


def _even_goals(people, qualified):
    """
    Return how many people every personality should get to spread them evenly.

    Some personalities can't get their equal share, because too few people qualify (e.g. only a few request songs).
    What they can't take is divided evenly over the others.
    """
    capacity = {
        key: amount * TUNING_MAX_SHARE_OF_QUALIFIED for key, amount in qualified.items()
    }
    goals = {}
    remaining = people
    for index, key in enumerate(sorted(capacity, key=capacity.get)):
        goals[key] = min(capacity[key], remaining / (len(capacity) - index))
        remaining -= goals[key]
    return goals


def model(period, since):
    """Return the (cached, anonymous) populations and boosts of a period."""

    def build():
        context = period_context(period, since)
        populations, boosts = tune(everyones_features(period, since, context), context)
        return {"populations": populations, "boosts": boosts}

    return cache.get_or_set(
        f"wrapped:personality:{period.start}:{since}", build, 60 * 60
    )


def percentile(population, value):
    """Return which share of a population has a lower value (ties count half)."""
    if not population:
        return 0
    lower, upper = bisect_left(population, value), bisect_right(population, value)
    return (lower + (upper - lower) / 2) / len(population)


def standing_out(f, populations, context):
    """Return, per dimension someone qualifies for, how much they stand out (their percentile)."""
    return {
        key: percentile(populations[key], value(f, context))
        for key, (qualifies, value) in DIMENSIONS.items()
        if qualifies(f, context) and populations[key]
    }


def _best(percentiles, boosts):
    return max(percentiles, key=lambda key: percentiles[key] + boosts[key])


def personality(f, period, since, suffix=""):
    """
    Return someone's personality.

    :return: dict with the ``key``, ``name``, ``description`` (including how they compare), what the personality
    ``means`` and ``tags``
    """
    context = period_context(period, since)
    tuned = model(period, since)
    percentiles = standing_out(f, tuned["populations"], context)
    key = _best(percentiles, tuned["boosts"]) if percentiles else "rare"
    name, description = PERSONALITIES[key]

    sentences = [description]
    if key in COMPARISONS:
        # Count how many have a lower value, so "more than X%" is true.
        population = tuned["populations"][key]
        lower = bisect_left(population, DIMENSIONS[key][1](f, context))
        share = round(100 * lower / len(population))
        if share >= 50:
            sentences.append(COMPARISONS[key].format(percentage=share, period=suffix))

    tags = [
        TAGS[other]
        for other, value in sorted(percentiles.items(), key=lambda item: -item[1])
        if other != key and other in TAGS and value >= TAG_MIN_PERCENTILE
    ][:1]
    if f["orders"] >= 2 and key != "mixer":
        flavour, amount = f["flavours"].most_common(1)[0]
        if f["products"] >= 3:
            tags.append("Explorer")
        elif amount / f["orders"] >= LOVER_MIN_SHARE:
            tags.append(f"{flavour.capitalize()} lover")
        elif f["products"] == 2:
            tags.append("50/50")
    if f["orders"] and key != "hopper":
        canteen, amount = f["canteens"].most_common(1)[0]
        if amount / f["orders"] >= TEAM_MIN_SHARE:
            tags.append(f"Team {canteen}")

    return {
        "key": key,
        "name": name,
        "description": " ".join(sentences),
        "means": f"{MEANINGS[key]} Everyone gets the personality they stand out in most, compared to everyone "
        "else in the canteens.",
        "tags": tags[:3],
    }
