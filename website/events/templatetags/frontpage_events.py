from django import template
from django.utils import timezone

from events import services
from events.models import Event

register = template.Library()


@register.inclusion_tag('events/frontpage.html', takes_context=True)
def render_frontpage_events(context):
    upcoming_events = Event.objects.filter(
        published=True,
        end__gte=timezone.now()
    ).order_by('end')

    try:
        upcoming = [{
                'event': x,
                'current_user_registration': services.is_user_registered(
                    context['user'], x),
            } for x in upcoming_events[:6]]
    except AttributeError:
        upcoming = [{
                'event': x,
                'current_user_registration': None
            } for x in upcoming_events[:6]]

    return {'upcoming': upcoming}
