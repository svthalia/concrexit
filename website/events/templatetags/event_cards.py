from django import template

from events.templatetags.frontpage_events import render_frontpage_events
from events.templatetags.frontpage_events import render_frontpage_registration_events

register = template.Library()


@register.inclusion_tag("events/event_cards.html", takes_context=True)
def render_event_cards(context, events=None):
    return render_frontpage_events(context, events)


@register.inclusion_tag("events/registration_events.html", takes_context=True)
def render_registration_event_cards(context, events=None):
    return render_frontpage_registration_events(context, events)
