from django import template
from django.utils import timezone
from django.utils.translation import gettext as _

from events import services
from events.models import Event

register = template.Library()


@register.inclusion_tag("events/frontpage_events.html", takes_context=True)
def render_frontpage_events(context, events=None):
    if events is None:
        events = Event.objects.filter(
            published=True,
            start__gte=timezone.now() - timezone.timedelta(hours=24),
            end__gte=timezone.now(),
        ).order_by("start")[:6]

    cards = []
    for event in events:
        user_registration = None

        if context["user"] and services.is_user_registered(context["user"], event):
            if services.user_registration_pending(context["user"], event):
                user_registration = {
                    "class": "pending-registration",
                    "text": _("In queue for this event"),
                }
            else:
                user_registration = {
                    "class": "has-registration",
                    "text": _("Registered for this event"),
                }
        elif event.registration_required:
            user_registration = {
                "class": "open-registration",
                "text": _("Not registered for this event"),
            }

        cards.append({"event": event, "current_user_registration": user_registration})

    return {"events": cards}
