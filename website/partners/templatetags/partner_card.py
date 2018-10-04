from django import template
from django.template.defaultfilters import striptags, truncatechars

from thaliawebsite.templatetags.bleach_tags import bleach
from thaliawebsite.templatetags.grid_item import grid_item

register = template.Library()


@register.inclusion_tag('includes/grid_item.html')
def partner_card(partner):
    image_url = ''
    if partner.logo:
        image_url = partner.logo.url

    meta_text = truncatechars(bleach(striptags(partner.company_profile)), 180)

    return grid_item(
        title=partner.name,
        meta_text='<p class="px-1">{}</p>'.format(meta_text),
        url=partner.get_absolute_url,
        image_url=image_url,
        class_name='partner-card',
    )
