from borrel import models


def available_products():
    """Get products that are available for order."""
    return models.Product.objects.filter(active=True)


def product_categories():
    """Get all categories."""
    return models.ProductCategory.objects.all()