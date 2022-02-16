from django import template

from education.models import Summary

register = template.Library()


@register.inclusion_tag("education/frontpage_summaries.html", takes_context=True)
def render_frontpage_summaries(context, summaries=None):
    if summaries is None:
        summaries = Summary.objects.filter(
            accepted=True, course__until__isnull=True
        ).order_by("?")[:6]

    return {"summaries": summaries}
