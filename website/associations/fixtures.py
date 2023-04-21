from associations.models import Association


def create_fixtures():
    """Create fixtures for the Associations app."""
    Association.objects.create(name="BeeVee")
    Association.objects.create(name="CognAC")
    Association.objects.create(name="Desda")
    Association.objects.create(name="Leonardo da Vinci")
    Association.objects.create(name="Marie Curie")
    Association.objects.create(name="Sigma")
    Association.objects.create(name="Thalia")
