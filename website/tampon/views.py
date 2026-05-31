from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, TemplateView
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from tampon.forms import TamponNotificationForm, ResolveForm
from tampon.models import (
    TamponNotification,
    Room,
    Restock,
    RestockItem,
    StockData,
)
from tampon.permissions import (
    TamponCommitteeMixin,
    is_tampon_committee_member,
)


class IndexView(TemplateView):
    """Index view for tampon."""

    template_name = "tampon/index.html"

    def get_context_data(self, **kwargs):
        """Add the form and committee permissions to the template context."""
        context = super().get_context_data(**kwargs)
        room_input = self.request.GET.get("room")
        room = Room.objects.filter(slug=room_input).first()

        if room:
            messages.info(
                self.request,
                f"You are submitting a notification for {room}.",
                extra_tags="TempMessage",
            )
        elif room_input:
            messages.error(
                self.request,
                "Something went wrong with the room number provided. Please select a valid room from the dropdown menu.",
                extra_tags="TempMessage",
            )
        context["form"] = kwargs.get(
            "form",
            TamponNotificationForm(initial={"room": room}),
        )
        context["can_view_notifications"] = is_tampon_committee_member(
            self.request.user
        )
        return context

    def post(self, request, *args, **kwargs):
        """Store a submitted notification."""
        form = TamponNotificationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! The committee has been notified.")
            return redirect("tampon:index")

        return self.render_to_response(self.get_context_data(form=form))


class NotificationsView(TamponCommitteeMixin, ListView):
    """Committee-only page with submitted tampon notifications."""

    template_name = "tampon/notifications.html"
    model = TamponNotification
    context_object_name = "notifications"

    def get_queryset(self):
        cutoff = timezone.now() - timedelta(weeks=2)
        return TamponNotification.objects.filter(
            Q(is_resolved=False) | Q(is_resolved=True, resolved_at__gte=cutoff)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resolve_form"] = ResolveForm()
        return context

    def post(self, request, *args, **kwargs):
        form = ResolveForm(request.POST)
        if form.is_valid():
            notification = get_object_or_404(
                TamponNotification, pk=request.POST.get("notification_id")
            )
            notification.mark_resolved()
            no_notifications = 1
            for other_notification in TamponNotification.objects.filter(
                room=notification.room, is_resolved=False
            ):
                other_notification.mark_resolved()
                no_notifications += 1
            restock = Restock.objects.create(
                room=notification.room,
                restocked_by=request.user,
            )
            for field_name, quantity in form.cleaned_data.items():
                if field_name.startswith("stock_"):
                    stock_id = int(field_name.split("_")[1])
                    stock_data = get_object_or_404(StockData, pk=stock_id)
                    RestockItem.objects.create(
                        restock=restock,
                        stock_data=stock_data,
                        quantity=quantity,
                    )
                    stock_data.stock_amount -= quantity
                    stock_data.save()

            if no_notifications > 1:
                messages.success(
                    request,
                    f"{no_notifications} notifications for {notification.room} resolved and restock recorded.",
                )
            else:
                messages.success(
                    request,
                    f"Notification for {notification.room} resolved and restock recorded.",
                )
        else:
            messages.error(
                request,
                "Invalid input. Please enter a valid quantity to resolve the notification.",
            )
        return redirect("tampon:notifications")
