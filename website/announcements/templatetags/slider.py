from django import template
from django.conf import settings

from announcements.models import Slide

register = template.Library()


@register.inclusion_tag("announcements/slider.html", takes_context=True)
def render_slider(context):
    return {
        "slides": [
            s
            for s in Slide.objects.all().order_by("order")
            if s.is_visible and (not s.members_only or context["request"].member)
        ],
        "slide_size": "slide",
    }
