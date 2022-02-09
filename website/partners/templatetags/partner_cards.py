from django import template
from django.conf import settings
from django.template.defaultfilters import striptags, truncatechars

from thaliawebsite.templatetags.bleach_tags import bleach
from thaliawebsite.templatetags.grid_item import grid_item
from utils.media.services import get_thumbnail_url
from partners.models import Vacancy

register = template.Library()


@register.inclusion_tag("includes/grid_item.html")
def partner_card(partner):
    """Return grid item showing partner."""
    image_url = ""
    if partner.logo:
        image_url = get_thumbnail_url(
            partner.logo, settings.THUMBNAIL_SIZES["medium"], fit=False
        )

    meta_text = truncatechars(bleach(striptags(partner.company_profile)), 80)

    return grid_item(
        title=partner.name,
        meta_text='<p class="px-2 d-none d-md-block">{}</p>'.format(meta_text),
        url=partner.get_absolute_url,
        image_url=image_url,
        class_name="partner-card contain-logo",
    )


@register.inclusion_tag("includes/grid_item.html")
def partner_image_card(image):
    """Return grid item showing partner image."""
    class_name = "partner-image-card"
    image_url = get_thumbnail_url(image, settings.THUMBNAIL_SIZES["medium"])

    return grid_item(
        title="",
        url=get_thumbnail_url(image, settings.THUMBNAIL_SIZES["large"], fit=False),
        image_url=image_url,
        class_name=class_name,
        anchor_attrs='data-fancybox="gallery"',
    )


@register.inclusion_tag("partners/vacancy_card.html")
def vacancy_card(vacancy):
    """Return grid item showing vacancy."""
    image_url = None
    if vacancy.get_company_logo():
        image_url = get_thumbnail_url(
            vacancy.get_company_logo(), settings.THUMBNAIL_SIZES["medium"], fit=False
        )

    description = truncatechars(bleach(striptags(vacancy.description)), 300)
    extra_class = "external-vacancy"
    url = "#vacancy-{}".format(vacancy.id)
    keywords = vacancy.keywords.split(",")
    location = vacancy.location
    if vacancy.partner:
        url = "{}#vacancy-{}".format(vacancy.partner.get_absolute_url(), vacancy.id)
        extra_class = ""

    return {
        "title": vacancy.title,
        "company_name": vacancy.get_company_name(),
        "image_url": image_url,
        "description": description,
        "location": location,
        "keywords": keywords,
        "url": url,
        "extra_class": extra_class,
    }
