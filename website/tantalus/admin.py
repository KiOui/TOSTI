from django.contrib import admin

from tantalus.forms import TantalusProductAdminForm, TantalusOrderVenueAdminForm
from tantalus.models import TantalusProduct, TantalusOrderVenue


@admin.register(TantalusProduct)
class TantalusProductAdmin(admin.ModelAdmin):
    """Tantalus Product Admin."""

    list_display = [
        "product",
        "tantalus_id",
    ]
    form = TantalusProductAdminForm


@admin.register(TantalusOrderVenue)
class TantalusOrderVenueAdmin(admin.ModelAdmin):
    """Tantalus Order Venue Admin."""

    list_display = [
        "order_venue",
        "endpoint_id",
    ]
    form = TantalusOrderVenueAdminForm
