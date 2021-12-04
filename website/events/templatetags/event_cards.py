from django import template
from django.utils import timezone

from events import services
from events.models import Event

register = template.Library()


@register.inclusion_tag("events/event_cards.html", takes_context=True)
def render_event_cards(context, events=None):
    if events is None:
        events = Event.objects.filter(
            published=True,
            start__gte=timezone.now() - timezone.timedelta(hours=24),
            end__gte=timezone.now(),
        ).order_by("start")[:6]

    try:
        cards = [
            {
                "event": x,
                "current_user_registration": services.is_user_registered(
                    context["user"], x
                ),
            }
            for x in events
        ]
    except AttributeError:
        cards = [{"event": x, "current_user_registration": None} for x in events]

    return {"events": cards}
