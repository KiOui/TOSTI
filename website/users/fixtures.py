from faker import Factory as FakerFactory


def create_fixtures():
    """Create random users."""
    _faker = FakerFactory.create("nl_NL")