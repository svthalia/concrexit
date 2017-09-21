from django import template
from django.utils import timezone

from events import services
from events.models import Event

register = template.Library()


@register.inclusion_tag('events/cards.html', takes_context=True)
def show_cards(context):
    upcoming_events = Event.objects.filter(
        published=True,
        end__gte=timezone.now()
    ).order_by('end')

    try:
        upcoming = [{
                'event': x,
                'current_user_registration': services.is_user_registered(
                    x, context['user']),
            } for x in upcoming_events[:4]]
    except AttributeError:
        upcoming = [{
                'event': x,
                'current_user_registration': None
            } for x in upcoming_events[:4]]

    return {'upcoming': upcoming}
