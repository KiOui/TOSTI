from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from transactions.models import Account


class TransactionHistoryTabView(LoginRequiredMixin, TemplateView):
    """Transaction history view."""

    template_name = "users/account.html"

    def get(self, request, **kwargs):
        """Get transaction history."""
        try:
            account = request.user.account
        except ObjectDoesNotExist:
            rendered_tab = render_to_string(
                "transactions/open_account.html",
                request=request,
            )
        else:
            transactions = account.transactions.order_by("-timestamp")
            page = request.GET.get("page", 1)
            paginator = Paginator(transactions, per_page=50)
            rendered_tab = render_to_string(
                "transactions/account_transaction_history.html",
                context={
                    "page_obj": paginator.get_page(page),
                    "account": account,
                },
            )

        return render(
            request,
            self.template_name,
            {
                "active": kwargs.get("active"),
                "tabs": kwargs.get("tabs"),
                "rendered_tab": rendered_tab,
            },
        )

    def post(self, request, **kwargs):
        """Create a new account."""
        Account.objects.get_or_create(user=self.request.user)
        return self.get(request, **kwargs)
