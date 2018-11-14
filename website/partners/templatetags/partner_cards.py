from django import template
from django.conf import settings
from django.template.defaultfilters import striptags, truncatechars

from thaliawebsite.templatetags.bleach_tags import bleach
from thaliawebsite.templatetags.grid_item import grid_item
from utils.templatetags.thumbnail import thumbnail

register = template.Library()


@register.inclusion_tag('includes/grid_item.html')
def partner_card(partner):
    image_url = ''
    if partner.logo:
        image_url = partner.logo.url

    meta_text = truncatechars(bleach(striptags(partner.company_profile)), 80)

    return grid_item(
        title=partner.name,
        meta_text='<p class="px-2 d-none d-md-block">{}</p>'.format(meta_text),
        url=partner.get_absolute_url,
        image_url=image_url,
        class_name='partner-card',
    )


@register.inclusion_tag('includes/grid_item.html')
def partner_image_card(image):
    class_name = 'partner-image-card'
    image_url = thumbnail(image, settings.THUMBNAIL_SIZES['medium'])

    return grid_item(
        title='',
        url=thumbnail(image, settings.THUMBNAIL_SIZES['large'], fit=False),
        image_url=image_url,
        class_name=class_name,
        anchor_attrs='data-fancybox="gallery"'
    )


@register.inclusion_tag('partners/vacancy_card.html')
def vacancy_card(vacancy):
    image_url = None
    if vacancy.get_company_logo():
        image_url = thumbnail(vacancy.get_company_logo(),
                              settings.THUMBNAIL_SIZES['medium'],
                              fit=False)

    description = truncatechars(bleach(striptags(vacancy.description)), 150)
    extra_class = 'external-vacancy'
    url = '#vacancy-{}'.format(vacancy.id)
    if vacancy.partner:
        url = '{}#vacancy-{}'.format(vacancy.partner.get_absolute_url(),
                                     vacancy.id)
        extra_class = ''

    return {
        'title': vacancy.title,
        'company_name': vacancy.get_company_name(),
        'image_url': image_url,
        'description': description,
        'url': url,
        'extra_class': extra_class,
    }
