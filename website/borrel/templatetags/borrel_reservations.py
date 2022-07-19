from django import template
from django.utils import timezone

register = template.Library()


@register.inclusion_tag("borrel/borrel_reservation_warning.html", takes_context=True)
def borrel_reservations_to_submit(context):
    """Render borrel reservations to submit."""
    user = context.get("user")
    if not user:
        return
    reservations = user.borrel_reservations_access.filter(
        submitted_at__isnull=True, accepted=True, start__lte=timezone.now()
    )
    return {"request": context.get("request"), "reservations": reservations}
