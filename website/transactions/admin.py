from autocompletefilter.admin import AutocompleteFilterMixin
from autocompletefilter.filters import AutocompleteListFilter
from django.contrib import admin
from django.contrib.admin import register
from import_export.admin import ExportMixin

from transactions.models import Account, Transaction


@register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin interface for the account model."""

    list_display = ("user", "balance")
    search_fields = ("user__username",)
    readonly_fields = ("balance",)
    ordering = ("user__username",)
    autocomplete_fields = ("user",)


@register(Transaction)
class TransactionAdmin(AutocompleteFilterMixin, ExportMixin, admin.ModelAdmin):
    """Admin interface for the transaction model."""

    list_display = ("account", "amount", "description", "processor", "timestamp")
    search_fields = ("account__user__username", "description", "processor__username")
    autocomplete_fields = ("account", "processor")
    readonly_fields = (
        "processor",
        "payable_content_type",
        "payable_object_id",
        "payable_object",
    )
    ordering = ("-timestamp",)
    list_filter = (
        ("account", AutocompleteListFilter),
        "timestamp",
        ("processor", AutocompleteListFilter),
    )

    def save_model(self, request, obj, form, change):
        """Set the processor to the current user when creating a new transaction."""
        if not change:
            obj.processor = request.user
            super().save_model(request, obj, form, change)
