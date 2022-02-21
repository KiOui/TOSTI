from venues import models


def active_venues():
    return models.Venue.objects.filter(active=True)