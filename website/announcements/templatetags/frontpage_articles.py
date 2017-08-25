from django import template

from announcements.models import FrontpageArticle

register = template.Library()


@register.inclusion_tag('announcements/frontpage_articles.html')
def render_frontpage_articles():
    return {'articles': [a for a in FrontpageArticle.objects.all()
                         if a.is_visible]}
