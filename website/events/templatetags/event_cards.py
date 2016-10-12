from django import template
from django.utils import timezone

from events.models import Event

register = template.Library()


@register.inclusion_tag('events/cards.html')
def show_cards():
    upcoming_events = Event.objects.filter(
        published=True,
        end__gte=timezone.now()
    ).order_by('end')
    return {'events': upcoming_events[:4]}
