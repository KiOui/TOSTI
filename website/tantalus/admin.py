from django.contrib import admin

from tantalus.forms import TantalusProductAdminForm
from tantalus.models import TantalusProduct


@admin.register(TantalusProduct)
class TantalusProductAdmin(admin.ModelAdmin):
    """Tantalus Product Admin."""

    list_display = [
        "product",
        "tantalus_id",
    ]
    form = TantalusProductAdminForm
