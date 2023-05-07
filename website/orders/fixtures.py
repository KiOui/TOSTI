import random

import django.db.utils
import faker_commerce
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from orders.models import OrderVenue, Product
from venues.models import Venue
from faker import Factory as FakerFactory

User = get_user_model()


def create_random_fixtures():
    """Create random fixtures."""
    create_order_venues()
    create_products()


def create_order_venues():
    """Create fixtures for OrderVenue's."""
    if Venue.objects.filter(name="Noordkantine").exists():
        OrderVenue.objects.create(venue=Venue.objects.get(name="Noordkantine"))

    if Venue.objects.filter(name="Zuidkantine").exists():
        OrderVenue.objects.create(venue=Venue.objects.get(name="Zuidkantine"))

    for venue in Venue.objects.all():
        if venue.name == "Noordkantine" or venue.name == "Zuidkantine":
            pass
        else:
            if random.randint(0, 1) == 1:
                OrderVenue.objects.create(venue=venue)


def create_products():
    """Create products."""
    faker = FakerFactory.create("en_GB")
    faker.add_provider(faker_commerce.Provider)

    tosti_cheese = Product.objects.create(
        name="Tosti Cheese",
        icon="cheese",
        current_price=0.5,
    )
    tosti_ham_cheese = Product.objects.create(
        name="Tosti Ham Cheese",
        icon="bacon",
        current_price=0.5,
    )

    if OrderVenue.objects.filter(venue__name="Noordkantine").exists():
        north_canteen = OrderVenue.objects.get(venue__name="Noordkantine")
        tosti_cheese.available_at.add(north_canteen)
        tosti_ham_cheese.available_at.add(north_canteen)

    if OrderVenue.objects.filter(venue__name="Zuidkantine").exists():
        south_canteen = OrderVenue.objects.get(venue__name="Zuidkantine")
        tosti_cheese.available_at.add(south_canteen)
        tosti_ham_cheese.available_at.add(south_canteen)

    for _ in range(0, 20):
        try:
            new_product = Product.objects.create(
                name=faker.ecommerce_name(),
                available=False if random.randint(0, 100) == 0 else True,
                current_price=(random.randint(0, 1000) / 100),
                orderable=False,
                ignore_shift_restrictions=True,
                max_allowed_per_shift=None,
            )
            amount_of_venues_available = random.randint(0, OrderVenue.objects.all().count())
            order_venues_available = OrderVenue.objects.order_by("?")[:amount_of_venues_available]
            for order_venue in order_venues_available:
                new_product.available_at.add(order_venue)
        except ValidationError:
            pass
        except django.db.utils.IntegrityError:
            pass

