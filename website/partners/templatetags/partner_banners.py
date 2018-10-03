from django import template

register = template.Library()


@register.inclusion_tag('partners/banners.html', takes_context=True)
def render_partner_banners(context):
    return {
        'partners': context['showcased_partners']
    }
