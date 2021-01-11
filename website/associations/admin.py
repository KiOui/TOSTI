from django.contrib import admin
from .models import Association


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    """Admin for Associations."""

    pass
