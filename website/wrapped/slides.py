"""
The community slides of TOSTI Wrapped.

Every slide is a dict with anonymous, aggregate statistics only (never data about individual users):

- ``kicker`` (str): short title of the slide.
- ``value`` (int or str): the headline, numbers are animated.
- ``text`` (str): sentence continuing the headline.
- ``ranking`` (optional list of ``{"label": str, "value": int or str}``): a ranked list.
- ``share`` (optional ``{"label": str, "value": int or str}``): the line this slide adds to the share image.
- ``order`` (int): where the slide goes in the story. Personal and community slides are shown mixed, so related
  slides (e.g. the busiest day of everyone, then your favourite day) follow each other.
"""

import calendar
from datetime import timedelta

from constance import config
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Sum
from django.db.models.functions import ExtractWeekDay, TruncDate
from django.template.defaultfilters import pluralize

from borrel.models import BorrelReservation, ReservationItem
from fridges.models import AccessLog
from orders.models import Order, Shift
from thaliedje.models import SpotifyArtist, SpotifyQueueItem, SpotifyTrack
from venues.models import Reservation

User = get_user_model()

# A tosti is roughly 2 cm thick.
TOSTI_HEIGHT_METRES = 0.02

# Drawing the tosti tower (in SVG units, see ``wrapped/illustrations/tower.html``).
TOWER_VISIBLE_TOSTIS = 8
TOWER_BASE_Y = 186
TOWER_TOSTI_HEIGHT = 18
CLOUD_METRES = 10

# English names of the canteens; other venues keep their own name.
CANTEEN_NAMES = {"Noordkantine": "North", "Zuidkantine": "South"}

# Show orders and tostis as one slide when at least this share of the orders were tostis.
MERGE_TOSTI_SHARE = 0.95


def ranked(queryset, label_field, limit=5):
    """Count the rows of a queryset per ``label_field`` and return the top ``limit`` as a slide ranking."""
    return [
        {"label": row[label_field], "value": row["amount"]}
        for row in queryset.values(label_field)
        .annotate(amount=Count("id"))
        .order_by("-amount")[:limit]
    ]


def tosti_tower(tostis):
    """Return how high a number of tostis would be when stacked, e.g. '12 metres'."""
    height = tostis * TOSTI_HEIGHT_METRES
    return (
        f"{height:,.0f} metres" if height >= 2 else f"{height * 100:,.0f} centimetres"
    )


def canteen_name(venue_name):
    """Return the English name of a canteen, e.g. 'Noordkantine' becomes 'North'."""
    return CANTEEN_NAMES.get(venue_name, venue_name)


def tower_illustration(tostis):
    """Return what to draw for a tower of tostis: at most a few tostis, and a tall tower disappears in the clouds."""
    return {
        "type": "tower",
        "stack": [
            {"index": index, "y": TOWER_BASE_Y - TOWER_TOSTI_HEIGHT * (index + 1)}
            for index in range(min(tostis, TOWER_VISIBLE_TOSTIS))
        ],
        "clouds": tostis * TOSTI_HEIGHT_METRES >= CLOUD_METRES,
    }


def times(amount):
    """Format how many times something happened, e.g. 4 becomes '4×'."""
    return f"{amount:,}×"


def busiest(queryset, expression):
    """Return the value of ``expression`` that occurs most in a queryset, with its count."""
    return (
        queryset.annotate(bucket=expression)
        .values("bucket")
        .annotate(amount=Count("id"))
        .order_by("-amount")
        .first()
    )


def weekday_name(extracted_weekday):
    """Return the name of a weekday from ``ExtractWeekDay`` (1 is Sunday, 7 is Saturday)."""
    return calendar.day_name[(extracted_weekday - 2) % 7]


def artist_names(track):
    """Return the artists of a track as a comma separated string."""
    return ", ".join(artist.artist_name for artist in track.track_artists.all())


def top_tracks(requests, limit=5):
    """Return the most requested tracks among a queryset of song requests, annotated with ``amount``."""
    return list(
        SpotifyTrack.objects.filter(requests__in=requests)
        .annotate(amount=Count("requests"))
        .order_by("-amount")
        .prefetch_related("track_artists")[:limit]
    )


def top_artists(requests, limit=5):
    """Return the most requested artists among a queryset of song requests, annotated with ``amount``."""
    return list(
        SpotifyArtist.objects.filter(spotifytrack__requests__in=requests)
        .annotate(amount=Count("spotifytrack__requests"))
        .order_by("-amount")[:limit]
    )


def newcomer_slides(period):
    """Slides about people joining TOSTI."""
    new_users = period.filter(User.objects.all(), "date_joined").count()
    if new_users == 0:
        return []
    text = "people logged in to TOSTI for the very first time. Welcome!"
    # Only the last login of every user is stored, so this is only right for the period that is still going on.
    if period.is_ongoing():
        logged_in = period.filter(User.objects.all(), "last_login").count()
        text += f" In total, {logged_in:,} {'person' if logged_in == 1 else 'people'} logged in this year."
    return [
        {
            "kicker": "Newcomers",
            "icon": "fa-hand",
            "icon_animation": "wave",
            "order": 10,
            "value": new_users,
            "text": text,
        }
    ]


def order_slides(period):
    """Slides about orders."""
    orders = period.filter(Order.objects.all(), "created")
    total = orders.count()
    if total == 0:
        return []

    shifts = period.filter(Shift.objects.all(), "start").count()
    spread = f"spread over {shifts:,} shift{pluralize(shifts)}"
    tostis = orders.filter(product__name__icontains="tosti").count()
    tower = f"Stacked on top of each other, that's a tower of {tosti_tower(tostis)}!"

    if tostis >= MERGE_TOSTI_SHARE * total:
        # (Almost) everything ordered was a tosti, so one slide says it all.
        slides = [
            {
                "kicker": "Tostis",
                "order": 20,
                "value": tostis,
                "text": f"tostis were grilled, {spread}. {tower}",
                "illustration": tower_illustration(tostis),
                "share": {"label": "Tostis grilled", "value": tostis},
            }
        ]
    else:
        slides = [
            {
                "kicker": "Orders",
                "icon": "fa-bread-slice",
                "icon_animation": "pop",
                "order": 20,
                "value": total,
                "text": f"items were ordered in the canteens, {spread}.",
                "share": {"label": "Orders in the canteens", "value": total},
            }
        ]
        if tostis:
            slides.append(
                {
                    "kicker": "Tostis",
                    "order": 21,
                    "value": tostis,
                    "text": f"of them were tostis. {tower}",
                    "illustration": tower_illustration(tostis),
                    "share": {"label": "Tostis grilled", "value": tostis},
                }
            )

    canteens = ranked(orders, "shift__venue__venue__name")
    if len(canteens) >= 2:
        slides.append(
            {
                "kicker": "The canteen battle",
                "order": 24,
                "value": canteen_name(canteens[0]["label"]),
                "text": f"won the battle, with {round(100 * canteens[0]['value'] / total)}% of all orders.",
                "illustration": {
                    "type": "battle",
                    "sides": [
                        {
                            "label": canteen_name(canteen["label"]),
                            "share": round(100 * canteen["value"] / total),
                        }
                        for canteen in canteens
                    ],
                },
                "ranking": [
                    {
                        "label": canteen_name(canteen["label"]),
                        "value": f"{canteen['value']:,} order{pluralize(canteen['value'])}",
                    }
                    for canteen in canteens
                ],
            }
        )

    top_products = ranked(orders, "product__name")
    slides.append(
        {
            "kicker": "Crowd favourites",
            "icon": "fa-crown",
            "icon_animation": "wave",
            "order": 40,
            "value": top_products[0]["label"],
            "text": f"was the most ordered product: {round(100 * top_products[0]['value'] / total)}% of all orders.",
            "ranking": [
                {"label": product["label"], "value": times(product["value"])}
                for product in top_products
            ],
            "share": {
                "label": "Product of the year",
                "value": top_products[0]["label"],
            },
        }
    )

    busiest_day = busiest(orders, TruncDate("created"))
    busiest_weekday = busiest(orders, ExtractWeekDay("created"))
    biggest_shift = busiest(orders, F("shift"))
    slides.append(
        {
            "kicker": "Rush hour",
            "icon": "fa-person-running",
            "icon_animation": "bounce",
            "order": 30,
            "value": f"{busiest_day['bucket'].day} {busiest_day['bucket']:%B}",
            "text": f"was the busiest day of the year, with {busiest_day['amount']:,} orders.",
            "ranking": [
                {
                    "label": "Busiest day of the week",
                    "value": weekday_name(busiest_weekday["bucket"]),
                },
                {"label": "Most orders in one shift", "value": biggest_shift["amount"]},
            ],
        }
    )

    waiting_time = (
        orders.filter(
            type=Order.TYPE_ORDERED,
            ready_at__isnull=False,
            # Ignore orders that were only marked ready long afterwards (e.g. forgotten ones).
            ready_at__lt=F("created") + timedelta(hours=1),
        )
        .annotate(
            waiting_time=ExpressionWrapper(
                F("ready_at") - F("created"), output_field=DurationField()
            )
        )
        .aggregate(average=Avg("waiting_time"))["average"]
    )
    if waiting_time is not None:
        slides.append(
            {
                "kicker": "Speedy service",
                "icon": "fa-stopwatch",
                "icon_animation": "pulse",
                "order": 50,
                "value": f"{waiting_time.total_seconds() / 60:.1f} min",
                "text": "was the average time between placing an order and it being ready. "
                "Thanks, shift volunteers!",
            }
        )

    top_associations = ranked(
        orders.filter(user_association__isnull=False), "user_association__name"
    )
    if top_associations:
        slides.append(
            {
                "kicker": "Association leaderboard",
                "icon": "fa-trophy",
                "icon_animation": "wave",
                "order": 55,
                "value": top_associations[0]["label"],
                "text": "was the hungriest association of the year.",
                "ranking": top_associations,
            }
        )

    return slides


def music_slides(period):
    """Slides about Thaliedje song requests."""
    requests = period.filter(SpotifyQueueItem.objects.all(), "added")
    total = requests.count()
    if total == 0:
        return []

    slides = [
        {
            "kicker": "Thaliedje",
            "icon": "fa-music",
            "icon_animation": "bounce",
            "order": 60,
            "value": total,
            "text": f"songs were requested, {requests.values('track').distinct().count():,} of them different.",
            "share": {"label": "Songs requested", "value": total},
        }
    ]
    # Only worth a battle when there was music in more than one canteen.
    canteens = ranked(
        requests.filter(player__venue__isnull=False), "player__venue__name"
    )
    if len(canteens) >= 2:
        slides[0]["ranking"] = [
            {
                "label": canteen_name(canteen["label"]),
                "value": f"{canteen['value']:,} song{pluralize(canteen['value'])}",
            }
            for canteen in canteens
        ]

    tracks = top_tracks(requests)
    if tracks:
        slides.append(
            {
                "kicker": "Song of the year",
                "icon": "fa-compact-disc",
                "icon_animation": "spin",
                "order": 62,
                "value": tracks[0].track_name,
                "text": f"by {artist_names(tracks[0])} was requested {tracks[0].amount:,} times.",
                "ranking": [
                    {
                        "label": f"{track.track_name} – {artist_names(track)}",
                        "value": times(track.amount),
                    }
                    for track in tracks
                ],
                "share": {
                    "label": "Song of the year",
                    "value": f"{tracks[0].track_name} – {artist_names(tracks[0])}",
                },
            }
        )

    artists = top_artists(requests)
    if artists:
        slides.append(
            {
                "kicker": "Artist of the year",
                "icon": "fa-microphone",
                "icon_animation": "wave",
                "order": 64,
                "value": artists[0].artist_name,
                "text": f"filled the canteens with music, with {artists[0].amount:,} requests.",
                "ranking": [
                    {"label": artist.artist_name, "value": times(artist.amount)}
                    for artist in artists
                ],
            }
        )

    return slides


def fridge_slides(period):
    """Slides about fridge openings."""
    openings = period.filter(AccessLog.objects.all(), "timestamp")
    total = openings.count()
    if total == 0:
        return []
    return [
        {
            "kicker": "Fridges",
            "icon": "fa-snowflake",
            "icon_animation": "spin",
            "order": 70,
            "value": total,
            "text": "times a fridge was unlocked with TOSTI.",
            "ranking": ranked(openings, "fridge__name"),
        }
    ]


def borrel_slides(period):
    """Slides about borrels."""
    borrels = period.filter(BorrelReservation.objects.filter(accepted=True), "start")
    total = borrels.count()
    if total == 0:
        return []

    slide = {
        "kicker": "Borrels",
        "icon": "fa-beer-mug-empty",
        "icon_animation": "wave",
        "order": 80,
        "value": total,
        "text": "borrels were held in the canteens.",
    }
    beers = ReservationItem.objects.filter(
        reservation__in=borrels,
        product__category_id=config.STATISTICS_BORREL_CATEGORY,
    ).aggregate(amount=Sum("amount_used"))["amount"]
    if beers:
        slide["ranking"] = [{"label": "Beers poured", "value": beers}]
    return [slide]


def reservation_slides(period):
    """Slides about venue reservations."""
    reservations = period.filter(Reservation.objects.filter(accepted=True), "start")
    total = reservations.count()
    if total == 0:
        return []
    return [
        {
            "kicker": "Reservations",
            "icon": "fa-users",
            "icon_animation": "pop",
            "order": 90,
            "value": total,
            "text": "venue reservations brought activities to the canteens.",
            "ranking": ranked(reservations, "venue__name"),
        }
    ]


SLIDE_GENERATORS = [
    newcomer_slides,
    order_slides,
    music_slides,
    fridge_slides,
    borrel_slides,
    reservation_slides,
]
