from django.template import Library

from events.models import FeedToken

register = Library()


@register.simple_tag(takes_context=True)
def personal_feed(context):
    """Return a personal token for the ical feed."""
    member = context["request"].user
    return FeedToken.objects.get_or_create(member=member)[0].token
